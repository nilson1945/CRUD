"""Cadastro de clientes e histórico vinculado."""

from __future__ import annotations

import customtkinter as ctk

import clientes
import tema
from interfaces.componentes import (
    Formulario, botao, confirmar, entrada, mensagem, painel, preencher,
    rotulo, selecionado_id, tabela,
)
from validacoes import formatar_data, formatar_moeda, parse_data


class TelaClientes(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color=tema.BG_CONTENT)
        self.app = app
        topo = painel(self)
        topo.pack(fill="x", padx=16, pady=16)
        rotulo(topo, "Clientes", 20, True).pack(side="left", padx=16, pady=12)
        self.busca = entrada(topo, width=260, placeholder_text="Nome, CPF ou telefone")
        self.busca.pack(side="right", padx=8, pady=12)
        botao(topo, "Pesquisar", self.recarregar, "secundario", width=110).pack(side="right")
        botao(topo, "Novo cliente", self._novo, width=130).pack(side="right", padx=8)

        self.tree = tabela(
            self,
            [
                ("ID", 50), ("Nome", 220), ("CPF", 130), ("Telefone", 120),
                ("Cidade", 140), ("Cadastro", 100), ("Situação", 80),
            ],
        )
        barra = ctk.CTkFrame(self, fg_color="transparent")
        barra.pack(fill="x", padx=16, pady=(0, 12))
        botao(barra, "Editar", self._editar, "secundario", width=110).pack(side="left", padx=4)
        botao(barra, "Histórico", self._historico, width=120).pack(side="left", padx=4)
        botao(barra, "Inativar", self._inativar, "secundario", width=110).pack(side="left", padx=4)
        botao(barra, "Excluir", self._excluir, "perigo", width=110).pack(side="left", padx=4)
        self.recarregar()

    def recarregar(self):
        rows = clientes.listar(self.busca.get())
        preencher(
            self.tree,
            [
                (
                    r["id"], r["nome"], r["cpf"] or "", r["telefone"] or "",
                    r["cidade"] or "", formatar_data(r["data_cadastro"]), r["situacao"],
                )
                for r in rows
            ],
            [r["id"] for r in rows],
        )

    def _form(self, dados=None):
        f = Formulario(self, "Cliente", 560, 700)
        d = dados or {}
        f.campo("nome", "Nome completo", d.get("nome", ""))
        f.campo("cpf", "CPF", d.get("cpf") or "")
        f.campo("rg", "RG", d.get("rg") or "")
        f.campo("data_nascimento", "Data de nascimento", formatar_data(d.get("data_nascimento")))
        f.campo("telefone", "Telefone", d.get("telefone") or "")
        f.campo("whatsapp", "WhatsApp", d.get("whatsapp") or "")
        f.campo("email", "E-mail", d.get("email") or "")
        f.campo("cep", "CEP", d.get("cep") or "")
        f.campo("endereco", "Endereço", d.get("endereco") or "")
        f.campo("numero", "Número", d.get("numero") or "")
        f.campo("bairro", "Bairro", d.get("bairro") or "")
        f.campo("cidade", "Cidade", d.get("cidade") or "")
        f.campo("estado", "Estado", d.get("estado") or "")
        f.campo("observacoes", "Observações", d.get("observacoes") or "", texto_longo=True)
        f.campo("situacao", "Situação", d.get("situacao") or "ativo", ["ativo", "inativo"])

        def salvar():
            p = {k: f.valor(k) for k in f.campos}
            p["data_nascimento"] = parse_data(p["data_nascimento"])
            if dados:
                p["id"] = dados["id"]
            try:
                clientes.salvar(p, self.app.sessao)
                mensagem(self, "Sucesso", "Cliente salvo com sucesso.")
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
            mensagem(self, "Atenção", "Selecione um cliente.", True)
            return
        self._form(clientes.obter(iid))

    def _inativar(self):
        iid = selecionado_id(self.tree)
        if iid and confirmar(self, "Inativar", "Inativar este cliente?"):
            clientes.inativar(iid, self.app.sessao)
            self.recarregar()

    def _excluir(self):
        iid = selecionado_id(self.tree)
        if not iid:
            return
        if not confirmar(self, "Excluir", "Excluir este cliente?"):
            return
        try:
            clientes.excluir(iid, self.app.sessao)
            self.recarregar()
        except ValueError as exc:
            mensagem(self, "Erro", str(exc), True)

    def _historico(self):
        iid = selecionado_id(self.tree)
        if not iid:
            mensagem(self, "Atenção", "Selecione um cliente.", True)
            return
        cli = clientes.obter(iid)
        top = ctk.CTkToplevel(self)
        top.title(f"Histórico — {cli['nome']}")
        top.geometry("820x520")
        top.configure(fg_color=tema.BG_APP)
        abas = ctk.CTkTabview(top, fg_color=tema.BG_PAINEL)
        abas.pack(fill="both", expand=True, padx=12, pady=12)
        t1 = abas.add("Matrículas / Cursos")
        t2 = abas.add("Pagamentos")
        t3 = abas.add("Lembretes")

        tree1 = tabela(t1, [("Matrícula", 120), ("Curso", 220), ("Data", 90), ("Valor", 90), ("Situação", 100)], 10)
        mats = clientes.historico_matriculas(iid)
        preencher(tree1, [
            (m["numero_matricula"], m["curso_nome"], formatar_data(m["data_matricula"]),
             formatar_moeda(m["valor_final"]), m["situacao"])
            for m in mats
        ])

        tree2 = tabela(t2, [("Data", 100), ("Matrícula", 120), ("Curso", 200), ("Valor", 100)], 10)
        pags = clientes.historico_pagamentos(iid)
        preencher(tree2, [
            (formatar_data(p["data_pagamento"]), p["numero_matricula"], p["curso_nome"],
             formatar_moeda(p["valor_pago"]))
            for p in pags
        ])

        tree3 = tabela(t3, [("Data", 90), ("Título", 240), ("Categoria", 140), ("Status", 90)], 10)
        lems = clientes.historico_lembretes(iid)
        preencher(tree3, [
            (formatar_data(l["data"]), l["titulo"], l["categoria"],
             "Concluído" if l["concluido"] else "Aberto")
            for l in lems
        ])
