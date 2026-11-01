"""Matrículas de clientes em cursos."""

from __future__ import annotations

from datetime import date

import customtkinter as ctk

import clientes
import cursos
import matriculas
import tema
from interfaces.componentes import (
    Formulario, botao, confirmar, entrada, mensagem, painel, preencher,
    rotulo, selecionado_id, tabela,
)
from validacoes import formatar_data, formatar_moeda, parse_data, parse_moeda


class TelaMatriculas(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color=tema.BG_CONTENT)
        self.app = app
        topo = painel(self)
        topo.pack(fill="x", padx=16, pady=16)
        rotulo(topo, "Matrículas", 20, True).pack(side="left", padx=16, pady=12)
        self.situacao = ctk.CTkComboBox(
            topo, values=["Todas"] + matriculas.SITUACOES, width=160,
            fg_color="white", text_color=tema.TXT,
        )
        self.situacao.set("Todas")
        self.situacao.pack(side="right", padx=8)
        self.busca = entrada(topo, width=220, placeholder_text="Cliente, curso ou número")
        self.busca.pack(side="right", padx=8, pady=12)
        botao(topo, "Pesquisar", self.recarregar, "secundario", width=110).pack(side="right")
        botao(topo, "Nova matrícula", self._novo, width=140).pack(side="right", padx=8)

        self.tree = tabela(
            self,
            [
                ("ID", 50), ("Número", 120), ("Cliente", 200), ("Curso", 220),
                ("Data", 90), ("Valor final", 100), ("Parcelas", 70), ("Situação", 110),
            ],
        )
        barra = ctk.CTkFrame(self, fg_color="transparent")
        barra.pack(fill="x", padx=16, pady=(0, 12))
        botao(barra, "Editar", self._editar, "secundario", width=110).pack(side="left", padx=4)
        botao(barra, "Gerar parcelas", self._parcelas, width=140).pack(side="left", padx=4)
        botao(barra, "Cancelar matrícula", self._cancelar, "perigo", width=160).pack(side="left", padx=4)
        self.recarregar()

    def recarregar(self):
        sit = self.situacao.get()
        sit = "" if sit == "Todas" else sit
        rows = matriculas.listar(self.busca.get(), sit)
        preencher(
            self.tree,
            [
                (
                    r["id"], r["numero_matricula"], r["cliente_nome"], r["curso_nome"],
                    formatar_data(r["data_matricula"]), formatar_moeda(r["valor_final"]),
                    r["qtd_parcelas"], r["situacao"],
                )
                for r in rows
            ],
            [r["id"] for r in rows],
        )

    def _form(self, dados=None):
        cli_lista = clientes.listar(incluir_inativos=False)
        cur_lista = cursos.listar(apenas_ativos=True)
        if not cli_lista:
            mensagem(self, "Atenção", "Cadastre um cliente antes de matricular.", True)
            return
        if not cur_lista:
            mensagem(self, "Atenção", "Não há cursos ativos.", True)
            return
        mapa_cli = {f"{c['id']} — {c['nome']}": c for c in cli_lista}
        mapa_cur = {f"{c['id']} — {c['nome']} ({formatar_moeda(c['valor_venda'])})": c for c in cur_lista}

        f = Formulario(self, "Matrícula", 580, 720)
        d = dados or {}
        cli_padrao = next(
            (k for k, v in mapa_cli.items() if v["id"] == d.get("cliente_id")),
            list(mapa_cli.keys())[0],
        )
        cur_padrao = next(
            (k for k, v in mapa_cur.items() if v["id"] == d.get("curso_id")),
            list(mapa_cur.keys())[0],
        )
        f.campo("cliente", "Cliente", cli_padrao, list(mapa_cli.keys()))
        f.campo("curso", "Curso", cur_padrao, list(mapa_cur.keys()))
        f.campo("data_matricula", "Data da matrícula", formatar_data(d.get("data_matricula")) or date.today().strftime("%d/%m/%Y"))
        f.campo("data_inicio", "Data de início", formatar_data(d.get("data_inicio")))
        f.campo("data_termino", "Data prevista de término", formatar_data(d.get("data_termino")))
        curso0 = mapa_cur[cur_padrao]
        f.campo("valor_original", "Valor original", d.get("valor_original") or curso0["valor_venda"])
        f.campo("desconto", "Desconto concedido", d.get("desconto") or 0)
        f.campo("valor_final", "Valor final negociado", d.get("valor_final") or curso0["valor_venda"])
        f.campo("qtd_parcelas", "Quantidade de parcelas", d.get("qtd_parcelas") or 12)
        f.campo("dia_vencimento", "Dia de vencimento", d.get("dia_vencimento") or 10)
        f.campo("forma_pagamento", "Forma de pagamento", d.get("forma_pagamento") or "PIX", matriculas.FORMAS)
        f.campo("situacao", "Situação", d.get("situacao") or "Ativa", matriculas.SITUACOES)
        f.campo("observacoes", "Observações", d.get("observacoes") or "", texto_longo=True)

        def ao_curso(_=None):
            cur = mapa_cur.get(f.valor("curso"))
            if cur and not dados:
                f.campos["valor_original"].delete(0, "end")
                f.campos["valor_original"].insert(0, str(cur["valor_venda"]))
                f.campos["valor_final"].delete(0, "end")
                f.campos["valor_final"].insert(0, str(cur["valor_venda"]))
                if cur.get("duracao_meses"):
                    f.campos["qtd_parcelas"].delete(0, "end")
                    f.campos["qtd_parcelas"].insert(0, str(cur["duracao_meses"]))

        f.campos["curso"].configure(command=ao_curso)

        def salvar():
            cli = mapa_cli.get(f.valor("cliente"))
            cur = mapa_cur.get(f.valor("curso"))
            if not cli or not cur:
                mensagem(f, "Erro", "Selecione cliente e curso.", True)
                return
            p = {
                "cliente_id": cli["id"],
                "curso_id": cur["id"],
                "data_matricula": parse_data(f.valor("data_matricula")),
                "data_inicio": parse_data(f.valor("data_inicio")),
                "data_termino": parse_data(f.valor("data_termino")),
                "valor_original": parse_moeda(f.valor("valor_original")),
                "desconto": parse_moeda(f.valor("desconto")) or 0,
                "valor_final": parse_moeda(f.valor("valor_final")),
                "qtd_parcelas": int(f.valor("qtd_parcelas") or 1),
                "dia_vencimento": int(f.valor("dia_vencimento") or 10),
                "forma_pagamento": f.valor("forma_pagamento"),
                "situacao": f.valor("situacao"),
                "observacoes": f.valor("observacoes"),
            }
            if dados:
                p["id"] = dados["id"]
                p["valor_original"] = dados["valor_original"]  # preserva contratado
            try:
                matriculas.salvar(p, self.app.sessao)
                mensagem(self, "Sucesso", "Matrícula registrada. Parcelas geradas automaticamente na inclusão.")
                f.destroy()
                self.recarregar()
            except (ValueError, Exception) as exc:
                mensagem(f, "Erro", str(exc), True)

        f.botoes(salvar)

    def _novo(self):
        self._form()

    def _editar(self):
        iid = selecionado_id(self.tree)
        if not iid:
            mensagem(self, "Atenção", "Selecione uma matrícula.", True)
            return
        self._form(matriculas.obter(iid))

    def _parcelas(self):
        iid = selecionado_id(self.tree)
        if not iid:
            return
        matriculas.gerar_parcelas_se_faltando(iid)
        mensagem(self, "Parcelas", "Parcelas conferidas. Se já existiam, nada foi duplicado.")

    def _cancelar(self):
        iid = selecionado_id(self.tree)
        if not iid:
            return
        if not confirmar(self, "Cancelar", "Cancelar a matrícula e as parcelas em aberto?"):
            return
        matriculas.cancelar(iid, self.app.sessao)
        self.recarregar()
