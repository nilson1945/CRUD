"""Tela de autenticação e cadastro de usuário do primeiro acesso."""

from __future__ import annotations

from typing import Optional

import customtkinter as ctk

import autenticacao
import tema
from database import obter_config
from funcionarios import criar_usuario_inicial, primeiro_acesso_pendente
from interfaces.componentes import botao, entrada, mensagem, rotulo

DICA_SENHA = "Esqueceu a senha? Solicite ao administrador a redefinição."


class TelaLogin(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.usuario = None
        self.title("Acesso — Sistema de Gestão")
        self.geometry("460x560")
        self.resizable(False, False)
        self.configure(fg_color=tema.BG_APP)
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self.quadro = ctk.CTkFrame(
            self, fg_color=tema.BG_PAINEL, corner_radius=16,
            border_width=1, border_color=tema.BORDA,
        )
        self.quadro.pack(fill="both", expand=True, padx=28, pady=28)

        rotulo(self.quadro, obter_config("nome_empresa", "Dimensão do Logus"), 20, True).pack(
            pady=(28, 4)
        )
        rotulo(self.quadro, "Gestão empresarial", 13, cor=tema.TXT_MUTED).pack()
        rotulo(self.quadro, "Entre com seu usuário e senha", 12, cor=tema.TXT_SUAVE).pack(
            pady=(18, 8)
        )

        rotulo(self.quadro, "Usuário", 12).pack(anchor="w", padx=40)
        self.ent_user = entrada(self.quadro, width=340)
        self.ent_user.pack(padx=40, pady=(0, 10))
        rotulo(self.quadro, "Senha", 12).pack(anchor="w", padx=40)
        self.ent_pass = entrada(self.quadro, width=340, show="*")
        self.ent_pass.pack(padx=40, pady=(0, 16))
        self.ent_pass.bind("<Return>", lambda e: self._entrar())

        botao(self.quadro, "Entrar", self._entrar, width=340).pack(pady=(4, 14))
        self.frame_rodape = ctk.CTkFrame(self.quadro, fg_color="transparent")
        self.frame_rodape.pack(fill="x")
        self._montar_rodape()
        self.ent_user.focus()

    def _montar_rodape(self):
        for widget in self.frame_rodape.winfo_children():
            widget.destroy()
        if primeiro_acesso_pendente():
            rotulo(self.frame_rodape, "Precisa criar o seu acesso?", 11, cor=tema.TXT_MUTED).pack(
                pady=(0, 6)
            )
            botao(
                self.frame_rodape, "Novo cadastro", self._novo_cadastro,
                "secundario", width=340,
            ).pack()
        else:
            rotulo(self.frame_rodape, DICA_SENHA, 11, cor=tema.TXT_MUTED).pack(pady=(0, 16))

    def _entrar(self):
        dados = autenticacao.autenticar(self.ent_user.get(), self.ent_pass.get())
        if not dados:
            mensagem(self, "Acesso negado", "Usuário ou senha inválidos.", erro=True)
            return
        self.usuario = dados
        self.destroy()

    def _novo_cadastro(self):
        usuario = abrir_novo_cadastro(self)
        if not usuario:
            return
        self._montar_rodape()
        self.ent_user.delete(0, "end")
        self.ent_user.insert(0, usuario)
        self.ent_pass.delete(0, "end")
        self.ent_pass.focus()
        mensagem(self, "Novo cadastro", "Cadastro concluído. Informe a senha para entrar.")


def abrir_novo_cadastro(master) -> Optional[str]:
    """Cadastro de usuário na tela inicial (primeiro acesso do sistema)."""
    criado = {"usuario": None}
    top = ctk.CTkToplevel(master)
    top.title("Novo cadastro")
    top.geometry("480x520")
    top.configure(fg_color=tema.BG_APP)
    top.transient(master)
    top.grab_set()

    corpo = ctk.CTkFrame(top, fg_color=tema.BG_PAINEL, corner_radius=12)
    corpo.pack(fill="both", expand=True, padx=14, pady=14)
    rotulo(corpo, "Novo cadastro", 18, True).pack(anchor="w", padx=20, pady=(18, 0))
    rotulo(
        corpo,
        "Crie o seu usuário de acesso ao sistema.",
        12, cor=tema.TXT_SUAVE,
    ).pack(anchor="w", padx=20, pady=(2, 10))

    campos: dict[str, ctk.CTkEntry] = {}

    def campo(chave: str, label: str, senha: bool = False):
        rotulo(corpo, label, 12).pack(anchor="w", padx=20, pady=(8, 2))
        e = entrada(corpo, width=380, show="*" if senha else "")
        e.pack(anchor="w", padx=20)
        campos[chave] = e

    campo("nome", "Nome completo *")
    campo("usuario", "Usuário de acesso *")
    campo("senha", "Senha (mínimo 8 caracteres) *", senha=True)
    campo("confirmar", "Confirmar senha *", senha=True)

    ctk.CTkLabel(
        corpo,
        text="Os demais usuários são cadastrados em Funcionários, pelo administrador.",
        text_color=tema.TXT_MUTED, wraplength=400, justify="left",
        font=ctk.CTkFont(family=tema.FONTE, size=11),
    ).pack(anchor="w", padx=20, pady=(14, 0))

    def salvar():
        if campos["senha"].get() != campos["confirmar"].get():
            mensagem(top, "Senha", "A confirmação da senha não confere.", erro=True)
            return
        dados = {chave: campos[chave].get() for chave in ("nome", "usuario", "senha")}
        try:
            criar_usuario_inicial(dados)
        except (ValueError, PermissionError) as exc:
            mensagem(top, "Novo cadastro", str(exc), erro=True)
            return
        criado["usuario"] = dados["usuario"].strip()
        mensagem(top, "Novo cadastro", "Cadastro concluído com sucesso.")
        top.destroy()

    linha = ctk.CTkFrame(corpo, fg_color="transparent")
    linha.pack(fill="x", padx=20, pady=18)
    botao(linha, "Cancelar", top.destroy, "secundario", width=140).pack(side="right", padx=4)
    botao(linha, "Concluir cadastro", salvar, width=180).pack(side="right", padx=4)

    top.wait_window()
    return criado["usuario"]


def solicitar_troca_senha(master, sessao: dict) -> bool:
    from autenticacao import alterar_senha

    ok = {"feito": False}
    top = ctk.CTkToplevel(master)
    top.title("Troca de senha provisória")
    top.geometry("440x320")
    top.configure(fg_color=tema.BG_APP)
    top.transient(master)
    top.grab_set()
    quadro = ctk.CTkFrame(top, fg_color=tema.BG_PAINEL, corner_radius=12)
    quadro.pack(fill="both", expand=True, padx=16, pady=16)
    rotulo(quadro, "Altere sua senha provisória", 16, True).pack(pady=(16, 8))
    rotulo(quadro, "A senha deve ter no mínimo 8 caracteres.", 12, cor=tema.TXT_SUAVE).pack()

    rotulo(quadro, "Senha atual", 12).pack(anchor="w", padx=30, pady=(12, 0))
    e1 = entrada(quadro, width=340, show="*")
    e1.pack()
    rotulo(quadro, "Nova senha", 12).pack(anchor="w", padx=30, pady=(8, 0))
    e2 = entrada(quadro, width=340, show="*")
    e2.pack()
    rotulo(quadro, "Confirmar nova senha", 12).pack(anchor="w", padx=30, pady=(8, 0))
    e3 = entrada(quadro, width=340, show="*")
    e3.pack()

    def salvar():
        if e2.get() != e3.get():
            mensagem(top, "Senha", "A confirmação não confere.", erro=True)
            return
        try:
            alterar_senha(sessao["id"], e1.get(), e2.get())
            sessao["senha_provisoria"] = 0
            ok["feito"] = True
            top.destroy()
        except ValueError as exc:
            mensagem(top, "Senha", str(exc), erro=True)

    botao(quadro, "Salvar nova senha", salvar, width=220).pack(pady=16)
    top.wait_window()
    return ok["feito"]
