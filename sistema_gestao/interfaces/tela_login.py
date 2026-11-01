"""Tela de autenticação e cadastro de primeiro acesso."""

from __future__ import annotations

from typing import Optional

import customtkinter as ctk

import autenticacao
import tema
from database import obter_config
from funcionarios import criar_primeiro_administrador, empresa_configurada
from interfaces.componentes import botao, entrada, mensagem, rotulo

CAMPOS_EMPRESA = (
    ("nome_empresa", "Nome da empresa *"),
    ("empresa_cnpj", "CNPJ"),
    ("empresa_telefone", "Telefone"),
    ("empresa_email", "E-mail"),
    ("empresa_endereco", "Endereço"),
    ("empresa_cidade", "Cidade"),
    ("empresa_estado", "UF"),
)


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

        primeiro_acesso = not empresa_configurada()
        empresa = obter_config("nome_empresa", "Dimensão do Logus")
        quadro = ctk.CTkFrame(
            self, fg_color=tema.BG_PAINEL, corner_radius=16,
            border_width=1, border_color=tema.BORDA,
        )
        quadro.pack(fill="both", expand=True, padx=28, pady=28)

        self.lbl_empresa = rotulo(quadro, empresa, 20, True)
        self.lbl_empresa.pack(pady=(28, 4))
        rotulo(quadro, "Gestão empresarial", 13, cor=tema.TXT_MUTED).pack()
        rotulo(quadro, "Entre com seu usuário e senha", 12, cor=tema.TXT_SUAVE).pack(pady=(18, 8))

        rotulo(quadro, "Usuário", 12).pack(anchor="w", padx=40)
        self.ent_user = entrada(quadro, width=340)
        self.ent_user.pack(padx=40, pady=(0, 10))
        rotulo(quadro, "Senha", 12).pack(anchor="w", padx=40)
        self.ent_pass = entrada(quadro, width=340, show="*")
        self.ent_pass.pack(padx=40, pady=(0, 16))
        self.ent_pass.bind("<Return>", lambda e: self._entrar())

        botao(quadro, "Entrar", self._entrar, width=340).pack(pady=(4, 14))

        self.frame_inicial = None
        self.frame_dica = None
        if primeiro_acesso:
            self.frame_inicial = ctk.CTkFrame(quadro, fg_color="transparent")
            self.frame_inicial.pack(fill="x")
            rotulo(self.frame_inicial, "Primeiro acesso", 11, cor=tema.TXT_MUTED).pack(pady=(0, 6))
            botao(
                self.frame_inicial, "Cadastrar empresa e usuário", self._cadastro_inicial,
                "secundario", width=340,
            ).pack()
        else:
            self.frame_dica = ctk.CTkFrame(quadro, fg_color="transparent")
            self.frame_dica.pack(fill="x")
            rotulo(
                self.frame_dica,
                "Esqueceu a senha? Solicite ao administrador a redefinição.",
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

    def _cadastro_inicial(self):
        usuario = abrir_cadastro_inicial(self)
        if not usuario:
            return
        self.lbl_empresa.configure(text=obter_config("nome_empresa", "Dimensão do Logus"))
        if self.frame_inicial is not None:
            self.frame_inicial.destroy()
            self.frame_inicial = None
            self.frame_dica = ctk.CTkFrame(self.lbl_empresa.master, fg_color="transparent")
            self.frame_dica.pack(fill="x")
            rotulo(
                self.frame_dica,
                "Esqueceu a senha? Solicite ao administrador a redefinição.",
                11, cor=tema.TXT_MUTED,
            ).pack(pady=(0, 16))
        self.ent_user.delete(0, "end")
        self.ent_user.insert(0, usuario)
        self.ent_pass.delete(0, "end")
        self.ent_pass.focus()
        mensagem(self, "Primeiro acesso", "Cadastro concluído. Informe a senha para entrar.")


def abrir_cadastro_inicial(master) -> Optional[str]:
    """Diálogo de primeiro acesso: cadastro da empresa e do primeiro administrador."""
    criado = {"usuario": None}
    top = ctk.CTkToplevel(master)
    top.title("Primeiro acesso — cadastro da empresa")
    top.geometry("560x700")
    top.configure(fg_color=tema.BG_APP)
    top.transient(master)
    top.grab_set()

    corpo = ctk.CTkScrollableFrame(top, fg_color=tema.BG_PAINEL, corner_radius=12)
    corpo.pack(fill="both", expand=True, padx=14, pady=14)
    rotulo(corpo, "Cadastro da empresa", 18, True).pack(anchor="w", padx=10, pady=(10, 0))
    rotulo(
        corpo,
        "Informe os dados da empresa e crie o primeiro usuário administrador.",
        12, cor=tema.TXT_SUAVE,
    ).pack(anchor="w", padx=10, pady=(2, 8))

    campos: dict[str, ctk.CTkEntry] = {}

    def campo(chave: str, label: str, senha: bool = False):
        rotulo(corpo, label, 12).pack(anchor="w", padx=10, pady=(8, 2))
        e = entrada(corpo, width=460, show="*" if senha else "")
        e.pack(anchor="w", padx=10)
        campos[chave] = e

    for chave, label in CAMPOS_EMPRESA:
        campo(chave, label)

    rotulo(corpo, "Primeiro usuário administrador", 16, True).pack(
        anchor="w", padx=10, pady=(18, 0)
    )
    campo("nome", "Nome do administrador *")
    campo("usuario", "Usuário de acesso *")
    campo("senha", "Senha (mínimo 8 caracteres) *", senha=True)
    campo("confirmar", "Confirmar senha *", senha=True)

    def salvar():
        if campos["senha"].get() != campos["confirmar"].get():
            mensagem(top, "Senha", "A confirmação da senha não confere.", erro=True)
            return
        empresa = {chave: campos[chave].get() for chave, _ in CAMPOS_EMPRESA}
        dados = {chave: campos[chave].get() for chave in ("nome", "usuario", "senha")}
        try:
            criar_primeiro_administrador(empresa, dados)
        except (ValueError, PermissionError) as exc:
            mensagem(top, "Primeiro acesso", str(exc), erro=True)
            return
        criado["usuario"] = dados["usuario"].strip()
        mensagem(top, "Primeiro acesso", "Cadastro concluído com sucesso.")
        top.destroy()

    linha = ctk.CTkFrame(corpo, fg_color="transparent")
    linha.pack(fill="x", padx=10, pady=16)
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
