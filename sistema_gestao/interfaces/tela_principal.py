"""Janela principal com menu lateral e área central."""

from __future__ import annotations

import customtkinter as ctk

import tema
from autenticacao import tem_permissao
from database import obter_config
from interfaces.componentes import mensagem, rotulo
from interfaces.tela_clientes import TelaClientes
from interfaces.tela_configuracoes import TelaConfiguracoes
from interfaces.tela_cursos import TelaCursos
from interfaces.tela_dashboard import TelaDashboard
from interfaces.tela_financeiro import TelaFinanceiro
from interfaces.tela_funcionarios import TelaFuncionarios
from interfaces.tela_lembretes import TelaLembretes
from interfaces.tela_login import solicitar_troca_senha
from interfaces.tela_matriculas import TelaMatriculas
from interfaces.tela_relatorios import TelaRelatorios
from lembrete import resumo_notificacoes

MENU = [
    ("dashboard", "Dashboard"),
    ("funcionarios", "Funcionários"),
    ("clientes", "Clientes"),
    ("cursos", "Cursos"),
    ("matriculas", "Matrículas"),
    ("financeiro", "Financeiro"),
    ("lembretes", "Lembretes"),
    ("relatorios", "Relatórios"),
    ("configuracoes", "Configurações"),
]

TELAS = {
    "dashboard": TelaDashboard,
    "funcionarios": TelaFuncionarios,
    "clientes": TelaClientes,
    "cursos": TelaCursos,
    "matriculas": TelaMatriculas,
    "financeiro": TelaFinanceiro,
    "lembretes": TelaLembretes,
    "relatorios": TelaRelatorios,
    "configuracoes": TelaConfiguracoes,
}


class TelaPrincipal(ctk.CTk):
    def __init__(self, sessao: dict):
        super().__init__()
        self.sessao = sessao
        empresa = obter_config("nome_empresa", "Dimensão do Logus")
        self.title(f"{empresa} — Gestão Empresarial")
        self.geometry("1280x760")
        self.minsize(1100, 640)
        self.configure(fg_color=tema.BG_APP)
        ctk.set_appearance_mode("light")

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(self, width=220, fg_color=tema.BG_SIDEBAR, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        rotulo(self.sidebar, empresa, 16, True, tema.TXT_CLARO).pack(padx=16, pady=(22, 4))
        rotulo(
            self.sidebar, sessao.get("nome", ""), 12, cor="#D1D5DB"
        ).pack(padx=16, pady=(0, 18))

        self.botoes_menu = {}
        for chave, titulo in MENU:
            if not tem_permissao(sessao, chave):
                continue
            btn = ctk.CTkButton(
                self.sidebar, text=titulo, anchor="w",
                fg_color="transparent", hover_color=tema.BG_SIDEBAR_HOVER,
                text_color=tema.TXT_CLARO, height=38, corner_radius=8,
                font=ctk.CTkFont(family=tema.FONTE, size=14),
                command=lambda c=chave: self.mostrar(c),
            )
            btn.pack(fill="x", padx=10, pady=2)
            self.botoes_menu[chave] = btn

        ctk.CTkButton(
            self.sidebar, text="Sair", anchor="w",
            fg_color="transparent", hover_color="#374151",
            text_color=tema.TXT_CLARO, height=38,
            command=self.destroy,
        ).pack(side="bottom", fill="x", padx=10, pady=16)

        self.conteudo = ctk.CTkFrame(self, fg_color=tema.BG_CONTENT, corner_radius=0)
        self.conteudo.grid(row=0, column=1, sticky="nsew")
        self.conteudo.grid_rowconfigure(0, weight=1)
        self.conteudo.grid_columnconfigure(0, weight=1)

        self.frames: dict[str, ctk.CTkFrame] = {}
        self.atual = None
        self.mostrar("dashboard" if tem_permissao(sessao, "dashboard") else next(iter(self.botoes_menu)))
        self.after(400, self._avisos_iniciais)

    def mostrar(self, chave: str):
        if not tem_permissao(self.sessao, chave):
            mensagem(self, "Acesso", "Você não tem permissão para este módulo.", True)
            return
        if chave not in self.frames:
            self.frames[chave] = TELAS[chave](self.conteudo, self)
            self.frames[chave].grid(row=0, column=0, sticky="nsew")
        for nome, fr in self.frames.items():
            if nome == chave:
                fr.grid()
                if hasattr(fr, "recarregar"):
                    fr.recarregar()
            else:
                fr.grid_remove()
        self.atual = chave
        for k, btn in self.botoes_menu.items():
            btn.configure(fg_color=tema.BG_SIDEBAR_ATIVO if k == chave else "transparent")

    def _avisos_iniciais(self):
        if self.sessao.get("senha_provisoria"):
            ok = solicitar_troca_senha(self, self.sessao)
            if not ok:
                mensagem(self, "Senha provisória", "Altere a senha em Configurações o quanto antes.")
        notes = resumo_notificacoes()
        n_atr = len(notes["atrasados"])
        n_hoje = len(notes["hoje"])
        if n_atr or n_hoje:
            mensagem(
                self,
                "Lembretes",
                f"Você tem {n_hoje} lembrete(s) para hoje e {n_atr} atrasado(s).",
            )
