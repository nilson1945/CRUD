"""Lembretes e compromissos dentro da aplicação principal."""

from __future__ import annotations

from datetime import date

import customtkinter as ctk

import clientes
import funcionarios
import lembrete
import matriculas
import tema
from interfaces.componentes import (
    Formulario, botao, confirmar, entrada, mensagem, painel, preencher,
    rotulo, selecionado_id, tabela,
)
from validacoes import formatar_data, parse_data


class TelaLembretes(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color=tema.BG_CONTENT)
        self.app = app
        self.alertas = ctk.CTkFrame(self, fg_color="transparent")
        self.alertas.pack(fill="x", padx=16, pady=(12, 0))

        topo = painel(self)
        topo.pack(fill="x", padx=16, pady=12)
        rotulo(topo, "Lembretes", 20, True).pack(side="left", padx=16, pady=12)
        self.busca = entrada(topo, width=240, placeholder_text="Título, cliente ou descrição")
        self.busca.pack(side="right", padx=8, pady=12)
        botao(topo, "Pesquisar", self.recarregar, "secundario", width=110).pack(side="right")
        botao(topo, "Novo lembrete", self._novo, width=140).pack(side="right", padx=8)

        self.tree = tabela(
            self,
            [
                ("ID", 50), ("Data", 90), ("Hora", 70), ("Título", 220),
                ("Categoria", 140), ("Prioridade", 90), ("Cliente", 160), ("Status", 90),
            ],
        )
        barra = ctk.CTkFrame(self, fg_color="transparent")
        barra.pack(fill="x", padx=16, pady=(0, 12))
        botao(barra, "Editar", self._editar, "secundario", width=110).pack(side="left", padx=4)
        botao(barra, "Concluir", self._concluir, "sucesso", width=110).pack(side="left", padx=4)
        botao(barra, "Reabrir", lambda: self._concluir(False), "secundario", width=110).pack(side="left", padx=4)
        botao(barra, "Excluir", self._excluir, "perigo", width=110).pack(side="left", padx=4)
        self.recarregar()

    def recarregar(self):
        for w in self.alertas.winfo_children():
            w.destroy()
        notes = lembrete.resumo_notificacoes()
        avisos = [
            ("Hoje", len(notes["hoje"]), tema.AZUL),
            ("Atrasados", len(notes["atrasados"]), tema.VERMELHO),
            ("Próximos 7 dias", len(notes["proximos"]), tema.AMARELO),
        ]
        for i, (t, n, cor) in enumerate(avisos):
            box = painel(self.alertas)
            box.pack(side="left", expand=True, fill="x", padx=6)
            rotulo(box, t, 12, cor=tema.TXT_MUTED).pack(anchor="w", padx=14, pady=(10, 0))
            rotulo(box, str(n), 22, True, cor).pack(anchor="w", padx=14, pady=(0, 10))

        rows = lembrete.listar(self.busca.get())
        preencher(
            self.tree,
            [
                (
                    r["id"], formatar_data(r["data"]), r["horario"] or "",
                    r["titulo"], r["categoria"], r["prioridade"],
                    r["cliente_nome"] or "",
                    "Concluído" if r["concluido"] else "Aberto",
                )
                for r in rows
            ],
            [r["id"] for r in rows],
        )

    def _form(self, dados=None):
        funcs = funcionarios.listar(incluir_inativos=False)
        clis = clientes.listar(incluir_inativos=False)
        mats = matriculas.listar()
        mf = {"(nenhum)": None}
        mf.update({f"{x['id']} — {x['nome']}": x["id"] for x in funcs})
        mc = {"(nenhum)": None}
        mc.update({f"{x['id']} — {x['nome']}": x["id"] for x in clis})
        mm = {"(nenhuma)": None}
        mm.update({f"{x['numero_matricula']} — {x['cliente_nome']}": x["id"] for x in mats})

        f = Formulario(self, "Lembrete", 540, 620)
        d = dados or {}
        f.campo("titulo", "Título", d.get("titulo", ""))
        f.campo("data", "Data (DD/MM/AAAA)", formatar_data(d.get("data")) or date.today().strftime("%d/%m/%Y"))
        f.campo("horario", "Horário (HH:MM)", d.get("horario") or "09:00")
        f.campo("prioridade", "Prioridade", d.get("prioridade") or "Média", lembrete.PRIORIDADES)
        f.campo("categoria", "Categoria", d.get("categoria") or "Compromisso", lembrete.CATEGORIAS)
        f.campo(
            "funcionario", "Funcionário",
            next((k for k, v in mf.items() if v == d.get("funcionario_id")), "(nenhum)"),
            list(mf.keys()),
        )
        f.campo(
            "cliente", "Cliente",
            next((k for k, v in mc.items() if v == d.get("cliente_id")), "(nenhum)"),
            list(mc.keys()),
        )
        f.campo(
            "matricula", "Matrícula",
            next((k for k, v in mm.items() if v == d.get("matricula_id")), "(nenhuma)"),
            list(mm.keys()),
        )
        f.campo("descricao", "Descrição", d.get("descricao") or "", texto_longo=True)

        def salvar():
            p = {
                "titulo": f.valor("titulo"),
                "data": parse_data(f.valor("data")),
                "horario": f.valor("horario"),
                "prioridade": f.valor("prioridade"),
                "categoria": f.valor("categoria"),
                "funcionario_id": mf.get(f.valor("funcionario")),
                "cliente_id": mc.get(f.valor("cliente")),
                "matricula_id": mm.get(f.valor("matricula")),
                "descricao": f.valor("descricao"),
            }
            if dados:
                p["id"] = dados["id"]
                p["concluido"] = dados.get("concluido")
            try:
                lembrete.salvar(p, self.app.sessao)
                mensagem(self, "Sucesso", "Lembrete salvo.")
                f.destroy()
                self.recarregar()
            except ValueError as exc:
                mensagem(f, "Erro", str(exc), True)

        f.botoes(salvar)

    def _novo(self):
        self._form()

    def _editar(self):
        iid = selecionado_id(self.tree)
        if not iid:
            mensagem(self, "Atenção", "Selecione um lembrete.", True)
            return
        self._form(lembrete.obter(iid))

    def _concluir(self, feito=True):
        iid = selecionado_id(self.tree)
        if not iid:
            return
        lembrete.concluir(iid, self.app.sessao, feito)
        self.recarregar()

    def _excluir(self):
        iid = selecionado_id(self.tree)
        if iid and confirmar(self, "Excluir", "Excluir este lembrete?"):
            lembrete.excluir(iid, self.app.sessao)
            self.recarregar()
