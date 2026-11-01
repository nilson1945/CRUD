"""Catálogo de cursos."""

from __future__ import annotations

import customtkinter as ctk

import cursos
import tema
from interfaces.componentes import (
    Formulario, botao, confirmar, entrada, mensagem, painel, preencher,
    rotulo, selecionado_id, tabela,
)
from validacoes import formatar_moeda, parse_moeda


class TelaCursos(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color=tema.BG_CONTENT)
        self.app = app
        topo = painel(self)
        topo.pack(fill="x", padx=16, pady=16)
        rotulo(topo, "Cursos", 20, True).pack(side="left", padx=16, pady=12)
        self.categoria = ctk.CTkComboBox(
            topo, values=["Todas", "Curso Técnico", "Preparatório Vestibular"], width=200,
            fg_color="white", text_color=tema.TXT,
        )
        self.categoria.set("Todas")
        self.categoria.pack(side="right", padx=8)
        self.busca = entrada(topo, width=200, placeholder_text="Pesquisar curso")
        self.busca.pack(side="right", padx=8, pady=12)
        botao(topo, "Pesquisar", self.recarregar, "secundario", width=110).pack(side="right")
        botao(topo, "Novo curso", self._novo, width=120).pack(side="right", padx=8)

        self.tree = tabela(
            self,
            [
                ("ID", 50), ("Nome", 280), ("Categoria", 170), ("Modalidade", 110),
                ("Mín.", 80), ("Máx.", 80), ("Venda", 90), ("Meses", 60), ("Situação", 80),
            ],
        )
        barra = ctk.CTkFrame(self, fg_color="transparent")
        barra.pack(fill="x", padx=16, pady=(0, 12))
        botao(barra, "Editar", self._editar, "secundario", width=120).pack(side="left", padx=4)
        botao(barra, "Inativar", self._inativar, "secundario", width=120).pack(side="left", padx=4)
        botao(barra, "Excluir", self._excluir, "perigo", width=120).pack(side="left", padx=4)
        self.recarregar()

    def recarregar(self):
        cat = self.categoria.get()
        cat = "" if cat == "Todas" else cat
        rows = cursos.listar(self.busca.get(), cat)
        preencher(
            self.tree,
            [
                (
                    r["id"], r["nome"], r["categoria"], r["modalidade"] or "",
                    formatar_moeda(r["valor_minimo"]), formatar_moeda(r["valor_maximo"]),
                    formatar_moeda(r["valor_venda"]), r["duracao_meses"] or "",
                    r["situacao"],
                )
                for r in rows
            ],
            [r["id"] for r in rows],
        )

    def _form(self, dados=None):
        f = Formulario(self, "Curso", 540, 620)
        d = dados or {}
        f.campo("nome", "Nome", d.get("nome", ""))
        f.campo(
            "categoria", "Categoria", d.get("categoria") or "Curso Técnico",
            ["Curso Técnico", "Preparatório Vestibular", "Outros"],
        )
        f.campo("modalidade", "Modalidade", d.get("modalidade") or "Presencial",
                ["Presencial", "Noturno", "Vespertino", "Matutino", "EAD"])
        f.campo("valor_minimo", "Valor mínimo estimado", d.get("valor_minimo") or "")
        f.campo("valor_maximo", "Valor máximo estimado", d.get("valor_maximo") or "")
        f.campo("valor_venda", "Valor de venda", d.get("valor_venda") or "")
        f.campo("duracao_meses", "Duração em meses", d.get("duracao_meses") or 12)
        f.campo("descricao", "Descrição", d.get("descricao") or "", texto_longo=True)
        f.campo("situacao", "Situação", d.get("situacao") or "ativo", ["ativo", "inativo"])

        def salvar():
            p = {k: f.valor(k) for k in f.campos}
            p["valor_minimo"] = parse_moeda(p["valor_minimo"]) or 0
            p["valor_maximo"] = parse_moeda(p["valor_maximo"]) or 0
            p["valor_venda"] = parse_moeda(p["valor_venda"])
            try:
                p["duracao_meses"] = int(p["duracao_meses"] or 12)
            except ValueError:
                mensagem(f, "Erro", "Duração inválida.", True)
                return
            if dados:
                p["id"] = dados["id"]
            try:
                cursos.salvar(p, self.app.sessao)
                mensagem(self, "Sucesso", "Curso salvo. Matrículas já feitas mantêm o valor negociado.")
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
            mensagem(self, "Atenção", "Selecione um curso.", True)
            return
        self._form(cursos.obter(iid))

    def _inativar(self):
        iid = selecionado_id(self.tree)
        if iid and confirmar(self, "Inativar", "Inativar este curso?"):
            cursos.inativar(iid, self.app.sessao)
            self.recarregar()

    def _excluir(self):
        iid = selecionado_id(self.tree)
        if not iid:
            return
        if not confirmar(self, "Excluir", "Excluir este curso do catálogo?"):
            return
        try:
            cursos.excluir(iid, self.app.sessao)
            self.recarregar()
        except ValueError as exc:
            mensagem(self, "Erro", str(exc), True)
