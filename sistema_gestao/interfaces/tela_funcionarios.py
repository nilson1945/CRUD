"""Tela de funcionários."""

from __future__ import annotations

import customtkinter as ctk

import funcionarios
import tema
from autenticacao import eh_admin
from database import PERMISSOES_ADMIN, PERMISSOES_FUNCIONARIO
from interfaces.componentes import (
    Formulario, botao, confirmar, entrada, mensagem, painel, preencher,
    rotulo, selecionado_id, tabela,
)
from validacoes import formatar_data, formatar_moeda, parse_data, parse_moeda


class TelaFuncionarios(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color=tema.BG_CONTENT)
        self.app = app
        topo = painel(self)
        topo.pack(fill="x", padx=16, pady=16)
        rotulo(topo, "Funcionários", 20, True).pack(side="left", padx=16, pady=12)
        self.busca = entrada(topo, width=240, placeholder_text="Nome, CPF ou usuário")
        self.busca.pack(side="right", padx=8, pady=12)
        botao(topo, "Pesquisar", self.recarregar, "secundario", width=110).pack(side="right", pady=12)
        if eh_admin(app.sessao):
            botao(topo, "Novo", self._novo, width=110).pack(side="right", padx=8, pady=12)

        self.tree = tabela(
            self,
            [
                ("ID", 50), ("Nome", 220), ("CPF", 130), ("Cargo", 140),
                ("Usuário", 120), ("Perfil", 120), ("Situação", 90),
            ],
        )
        barra = ctk.CTkFrame(self, fg_color="transparent")
        barra.pack(fill="x", padx=16, pady=(0, 12))
        botao(barra, "Consultar / Editar", self._editar, "secundario", width=160).pack(side="left", padx=4)
        if eh_admin(app.sessao):
            botao(barra, "Inativar", self._inativar, "secundario", width=110).pack(side="left", padx=4)
            botao(barra, "Excluir", self._excluir, "perigo", width=110).pack(side="left", padx=4)
        self.recarregar()

    def recarregar(self):
        rows = funcionarios.listar(self.busca.get())
        preencher(
            self.tree,
            [
                (r["id"], r["nome"], r["cpf"] or "", r["cargo"] or "",
                 r["usuario"] or "", r["tipo_usuario"], r["situacao"])
                for r in rows
            ],
            [r["id"] for r in rows],
        )

    def _form(self, dados=None):
        if not eh_admin(self.app.sessao):
            mensagem(self, "Permissão", "Somente o administrador cadastra ou edita funcionários.", True)
            return
        f = Formulario(self, "Funcionário" if not dados else "Editar funcionário", 560, 680)
        d = dados or {}
        f.campo("nome", "Nome completo", d.get("nome", ""))
        f.campo("cpf", "CPF", d.get("cpf") or "")
        f.campo("rg", "RG", d.get("rg") or "")
        f.campo("data_nascimento", "Data de nascimento (DD/MM/AAAA)", formatar_data(d.get("data_nascimento")))
        f.campo("telefone", "Telefone", d.get("telefone") or "")
        f.campo("email", "E-mail", d.get("email") or "")
        f.campo("endereco", "Endereço", d.get("endereco") or "")
        f.campo("cargo", "Cargo", d.get("cargo") or "")
        f.campo("data_admissao", "Data de admissão", formatar_data(d.get("data_admissao")))
        f.campo("salario", "Salário", formatar_moeda(d.get("salario")) if d.get("salario") else "")
        f.campo("usuario", "Usuário de acesso", d.get("usuario") or "")
        f.campo("senha", "Senha de acesso" + (" (em branco para manter)" if dados else ""), senha=True)
        f.campo("tipo_usuario", "Tipo de usuário", d.get("tipo_usuario") or "funcionario",
                ["administrador", "funcionario"])
        f.campo("situacao", "Situação", d.get("situacao") or "ativo", ["ativo", "inativo"])

        def salvar():
            payload = {k: f.valor(k) for k in f.campos}
            payload["data_nascimento"] = parse_data(payload["data_nascimento"])
            payload["data_admissao"] = parse_data(payload["data_admissao"])
            payload["salario"] = parse_moeda(payload["salario"])
            if dados:
                payload["id"] = dados["id"]
                if not payload["senha"]:
                    payload.pop("senha")
            payload["permissoes"] = (
                PERMISSOES_ADMIN if payload["tipo_usuario"] == "administrador"
                else PERMISSOES_FUNCIONARIO
            )
            try:
                funcionarios.salvar(payload, self.app.sessao)
                mensagem(self, "Sucesso", "Funcionário salvo com sucesso.")
                f.destroy()
                self.recarregar()
            except (ValueError, PermissionError) as exc:
                mensagem(f, "Erro", str(exc), True)

        f.botoes(salvar)

    def _novo(self):
        self._form()

    def _editar(self):
        iid = selecionado_id(self.tree)
        if not iid:
            mensagem(self, "Atenção", "Selecione um funcionário.", True)
            return
        dados = funcionarios.obter(iid)
        if dados:
            self._form(dados)

    def _inativar(self):
        iid = selecionado_id(self.tree)
        if not iid:
            return
        if not confirmar(self, "Inativar", "Deseja inativar este funcionário?"):
            return
        try:
            funcionarios.inativar(iid, self.app.sessao)
            self.recarregar()
        except (ValueError, PermissionError) as exc:
            mensagem(self, "Erro", str(exc), True)

    def _excluir(self):
        iid = selecionado_id(self.tree)
        if not iid:
            return
        if not confirmar(self, "Excluir", "Excluir definitivamente este funcionário?"):
            return
        try:
            funcionarios.excluir(iid, self.app.sessao)
            self.recarregar()
        except (ValueError, PermissionError) as exc:
            mensagem(self, "Erro", str(exc), True)
