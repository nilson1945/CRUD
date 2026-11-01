"""Tela de autenticação."""

from __future__ import annotations

import customtkinter as ctk

import autenticacao
import tema
from database import obter_config
from interfaces.componentes import botao, entrada, mensagem, rotulo


class TelaLogin(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.usuario = None
        self.title("Acesso — Sistema de Gestão")
        self.geometry("460x420")
        self.resizable(False, False)
        self.configure(fg_color=tema.BG_APP)
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        empresa = obter_config("nome_empresa", "Dimensão do Logus")
        quadro = ctk.CTkFrame(
            self, fg_color=tema.BG_PAINEL, corner_radius=16,
            border_width=1, border_color=tema.BORDA,
        )
        quadro.pack(fill="both", expand=True, padx=28, pady=28)

        rotulo(quadro, empresa, 20, True).pack(pady=(28, 4))
        rotulo(quadro, "Gestão empresarial", 13, cor=tema.TXT_MUTED).pack()
        rotulo(quadro, "Entre com seu usuário e senha", 12, cor=tema.TXT_SUAVE).pack(pady=(18, 8))

        rotulo(quadro, "Usuário ou e-mail", 12).pack(anchor="w", padx=40)
        self.ent_user = entrada(quadro, width=340)
        self.ent_user.pack(padx=40, pady=(0, 10))
        rotulo(quadro, "Senha", 12).pack(anchor="w", padx=40)
        self.ent_pass = entrada(quadro, width=340, show="*")
        self.ent_pass.pack(padx=40, pady=(0, 16))
        self.ent_pass.bind("<Return>", lambda e: self._entrar())

        botao(quadro, "Entrar", self._entrar, width=340).pack(pady=(4, 20))
        rotulo(
            quadro,
            "Primeiro acesso: usuário admin (altere a senha provisória).",
            11, cor=tema.TXT_MUTED,
        ).pack(pady=(0, 16))
        self.ent_user.focus()

    def _entrar(self):
        dados = autenticacao.autenticar(self.ent_user.get(), self.ent_pass.get())
        if not dados:
            mensagem(self, "Acesso negado", "Usuário ou senha inválidos.", erro=True)
            return
        self.usuario = dados
        self.destroy()


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
