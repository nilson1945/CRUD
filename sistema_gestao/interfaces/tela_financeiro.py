"""Controle de parcelas e pagamentos."""

from __future__ import annotations

from datetime import date

import customtkinter as ctk

import financeiro
import tema
from interfaces.componentes import (
    Formulario, botao, card_kpi, entrada, mensagem, painel, preencher,
    rotulo, selecionado_id, tabela,
)
from validacoes import formatar_data, formatar_moeda, parse_data, parse_moeda


class TelaFinanceiro(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color=tema.BG_CONTENT)
        self.app = app
        self.kpis = ctk.CTkFrame(self, fg_color="transparent")
        self.kpis.pack(fill="x", padx=12, pady=(12, 0))

        topo = painel(self)
        topo.pack(fill="x", padx=16, pady=12)
        rotulo(topo, "Financeiro", 20, True).pack(side="left", padx=16, pady=12)
        self.filtro = ctk.CTkComboBox(
            topo,
            values=["todas", "pendentes", "vencidas", "a_vencer", "pagas"],
            width=150, fg_color="white", text_color=tema.TXT,
        )
        self.filtro.set("pendentes")
        self.filtro.pack(side="right", padx=8)
        self.busca = entrada(topo, width=220, placeholder_text="Cliente ou matrícula")
        self.busca.pack(side="right", padx=8, pady=12)
        botao(topo, "Atualizar", self.recarregar, "secundario", width=110).pack(side="right")

        self.tree = tabela(
            self,
            [
                ("ID", 50), ("Cliente", 180), ("Matrícula", 110), ("Parcela", 70),
                ("Vencimento", 100), ("Valor", 90), ("Pago", 90), ("Situação", 90),
            ],
        )
        barra = ctk.CTkFrame(self, fg_color="transparent")
        barra.pack(fill="x", padx=16, pady=(0, 12))
        botao(barra, "Registrar pagamento", self._pagar, width=170).pack(side="left", padx=4)
        botao(barra, "Juros / multa / desconto", self._encargos, "secundario", width=190).pack(side="left", padx=4)
        self.recarregar()

    def recarregar(self):
        for w in self.kpis.winfo_children():
            w.destroy()
        ind = financeiro.indicadores()
        itens = [
            ("Recebido no mês", formatar_moeda(ind["recebido_mes"])),
            ("A receber", formatar_moeda(ind["a_receber"])),
            ("Em atraso", formatar_moeda(ind["atraso"])),
            ("Pagamentos (geral)", formatar_moeda(ind["total_pagamentos"])),
        ]
        self.kpis.grid_columnconfigure((0, 1, 2, 3), weight=1)
        for i, (t, v) in enumerate(itens):
            card_kpi(self.kpis, t, v).grid(row=0, column=i, padx=8, sticky="ew")

        rows = financeiro.listar_parcelas(self.filtro.get(), self.busca.get())
        preencher(
            self.tree,
            [
                (
                    r["id"], r["cliente_nome"], r["numero_matricula"], r["numero"],
                    formatar_data(r["data_vencimento"]), formatar_moeda(r["valor_devido"]),
                    formatar_moeda(r["valor_pago"]), r["situacao"],
                )
                for r in rows
            ],
            [r["id"] for r in rows],
        )

    def _pagar(self):
        iid = selecionado_id(self.tree)
        if not iid:
            mensagem(self, "Atenção", "Selecione uma parcela.", True)
            return
        p = financeiro.obter_parcela(iid)
        f = Formulario(self, f"Pagamento — {p['cliente_nome']}", 480, 420)
        f.campo("valor", "Valor pago", p["valor"])
        f.campo("data", "Data do pagamento", date.today().strftime("%d/%m/%Y"))
        f.campo("forma", "Forma de pagamento", "PIX", financeiro.FORMAS)
        f.campo("obs", "Observação", "", texto_longo=True)

        def salvar():
            try:
                financeiro.registrar_pagamento(
                    iid, f.valor("valor"), f.valor("forma"),
                    parse_data(f.valor("data")), f.valor("obs"), self.app.sessao,
                )
                mensagem(self, "Sucesso", "Pagamento registrado.")
                f.destroy()
                self.recarregar()
            except ValueError as exc:
                mensagem(f, "Erro", str(exc), True)

        f.botoes(salvar)

    def _encargos(self):
        iid = selecionado_id(self.tree)
        if not iid:
            mensagem(self, "Atenção", "Selecione uma parcela.", True)
            return
        p = financeiro.obter_parcela(iid)
        f = Formulario(self, "Encargos da parcela", 440, 360)
        f.campo("juros", "Juros", p.get("juros") or 0)
        f.campo("multa", "Multa", p.get("multa") or 0)
        f.campo("desconto", "Desconto", p.get("desconto") or 0)

        def salvar():
            financeiro.aplicar_encargos(
                iid,
                parse_moeda(f.valor("juros")) or 0,
                parse_moeda(f.valor("multa")) or 0,
                parse_moeda(f.valor("desconto")) or 0,
                self.app.sessao,
            )
            mensagem(self, "Sucesso", "Encargos atualizados.")
            f.destroy()
            self.recarregar()

        f.botoes(salvar)
