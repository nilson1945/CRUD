"""Configurações, backup, restauração e histórico de ações."""

from __future__ import annotations

from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

import autenticacao
import tema
from database import (
    backup_banco,
    get_connection,
    obter_config,
    restaurar_banco,
    salvar_config,
)
from interfaces.componentes import botao, confirmar, entrada, mensagem, painel, preencher, rotulo, tabela
from validacoes import formatar_data


class TelaConfiguracoes(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color=tema.BG_CONTENT)
        self.app = app
        rotulo(self, "Configurações", 22, True).pack(anchor="w", padx=20, pady=(16, 8))

        box = painel(self)
        box.pack(fill="x", padx=16, pady=8)
        rotulo(box, "Empresa", 15, True).pack(anchor="w", padx=14, pady=(12, 4))
        self.nome = entrada(box, width=400)
        self.nome.insert(0, obter_config("nome_empresa", "Dimensão do Logus"))
        self.nome.pack(anchor="w", padx=14, pady=4)
        botao(box, "Salvar nome da empresa", self._salvar_nome, width=220).pack(anchor="w", padx=14, pady=(6, 14))

        box2 = painel(self)
        box2.pack(fill="x", padx=16, pady=8)
        rotulo(box2, "Segurança e backup", 15, True).pack(anchor="w", padx=14, pady=(12, 4))
        linha = ctk.CTkFrame(box2, fg_color="transparent")
        linha.pack(anchor="w", padx=14, pady=(4, 14))
        botao(linha, "Alterar minha senha", self._senha, "secundario", width=180).pack(side="left", padx=4)
        botao(linha, "Backup do banco", self._backup, width=160).pack(side="left", padx=4)
        botao(linha, "Restaurar backup", self._restaurar, "perigo", width=160).pack(side="left", padx=4)

        box3 = painel(self)
        box3.pack(fill="both", expand=True, padx=16, pady=8)
        rotulo(box3, "Histórico de ações administrativas", 15, True).pack(anchor="w", padx=14, pady=10)
        self.tree = tabela(
            box3,
            [("Quando", 150), ("Usuário", 80), ("Ação", 120), ("Tabela", 110), ("Detalhes", 280)],
            12,
        )
        self.recarregar()

    def recarregar(self):
        with get_connection() as con:
            rows = con.execute(
                """
                SELECT h.*, f.usuario
                FROM historico_acoes h
                LEFT JOIN funcionarios f ON f.id = h.usuario_id
                ORDER BY h.id DESC LIMIT 200
                """
            ).fetchall()
        preencher(
            self.tree,
            [
                (r["data_hora"], r["usuario"] or "", r["acao"], r["tabela"] or "", (r["detalhes"] or "")[:80])
                for r in rows
            ],
        )

    def _salvar_nome(self):
        salvar_config("nome_empresa", self.nome.get().strip() or "Dimensão do Logus")
        mensagem(self, "Configurações", "Nome da empresa atualizado.")

    def _senha(self):
        from interfaces.tela_login import solicitar_troca_senha
        # reutiliza diálogo exigindo senha atual via alterar_senha
        top = ctk.CTkToplevel(self)
        top.title("Alterar senha")
        top.geometry("420x280")
        top.configure(fg_color=tema.BG_APP)
        quadro = painel(top)
        quadro.pack(fill="both", expand=True, padx=12, pady=12)
        rotulo(quadro, "Senha atual", 12).pack(anchor="w", padx=16, pady=(12, 0))
        a = entrada(quadro, show="*", width=320)
        a.pack()
        rotulo(quadro, "Nova senha", 12).pack(anchor="w", padx=16, pady=(8, 0))
        b = entrada(quadro, show="*", width=320)
        b.pack()
        rotulo(quadro, "Confirmar", 12).pack(anchor="w", padx=16, pady=(8, 0))
        c = entrada(quadro, show="*", width=320)
        c.pack()

        def ok():
            if b.get() != c.get():
                mensagem(top, "Senha", "Confirmação não confere.", True)
                return
            try:
                autenticacao.alterar_senha(self.app.sessao["id"], a.get(), b.get())
                mensagem(self, "Senha", "Senha alterada.")
                top.destroy()
            except ValueError as exc:
                mensagem(top, "Erro", str(exc), True)

        botao(quadro, "Salvar", ok, width=160).pack(pady=14)

    def _backup(self):
        path = backup_banco()
        mensagem(self, "Backup", f"Cópia salva em:\n{path}")

    def _restaurar(self):
        if not confirmar(self, "Restaurar", "A restauração substitui os dados atuais. Continuar?"):
            return
        arq = filedialog.askopenfilename(filetypes=[("Banco SQLite", "*.db")])
        if not arq:
            return
        restaurar_banco(Path(arq))
        mensagem(self, "Restauração", "Backup restaurado. Reinicie o sistema para recarregar tudo.")
