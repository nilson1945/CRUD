"""Componentes visuais reutilizáveis."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

import customtkinter as ctk

import tema
from validacoes import formatar_data, formatar_moeda


def configurar_treeview() -> None:
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    style.configure(
        "Gestao.Treeview",
        background="white",
        fieldbackground="white",
        foreground=tema.TXT,
        rowheight=28,
        font=(tema.FONTE, 10),
        bordercolor=tema.BORDA,
    )
    style.configure(
        "Gestao.Treeview.Heading",
        background="#D1D5DB",
        foreground=tema.TXT,
        font=(tema.FONTE, 10, "bold"),
        relief="flat",
    )
    style.map("Gestao.Treeview", background=[("selected", tema.AZUL)])
    style.map("Gestao.Treeview.Heading", background=[("active", "#9CA3AF")])


def botao(master, texto: str, comando, tipo: str = "primario", **kw):
    cores = {
        "primario": (tema.AZUL, tema.AZUL_HOVER),
        "secundario": (tema.CINZA_BTN, tema.CINZA_BTN_HOVER),
        "perigo": (tema.VERMELHO, "#B91C1C"),
        "sucesso": (tema.VERDE, "#047857"),
    }
    fg, hover = cores.get(tipo, cores["primario"])
    return ctk.CTkButton(
        master, text=texto, command=comando,
        fg_color=fg, hover_color=hover, text_color="white",
        corner_radius=8, height=36, font=ctk.CTkFont(family=tema.FONTE, size=13),
        **kw,
    )


def entrada(master, **kw):
    return ctk.CTkEntry(
        master, fg_color="white", border_color=tema.BORDA, text_color=tema.TXT,
        corner_radius=8, height=34, **kw,
    )


def rotulo(master, texto: str, tamanho=13, negrito=False, cor=None):
    return ctk.CTkLabel(
        master, text=texto, text_color=cor or tema.TXT,
        font=ctk.CTkFont(family=tema.FONTE, size=tamanho, weight="bold" if negrito else "normal"),
    )


def painel(master, **kw):
    return ctk.CTkFrame(
        master, fg_color=tema.BG_PAINEL, corner_radius=12,
        border_width=1, border_color=tema.BORDA, **kw,
    )


def card_kpi(master, titulo: str, valor: str, sub: str = ""):
    box = painel(master)
    rotulo(box, titulo, 12, cor=tema.TXT_MUTED).pack(anchor="w", padx=16, pady=(12, 0))
    rotulo(box, valor, 22, True).pack(anchor="w", padx=16, pady=(4, 4 if sub else 12))
    if sub:
        rotulo(box, sub, 11, cor=tema.TXT_SUAVE).pack(anchor="w", padx=16, pady=(0, 12))
    return box


def mensagem(master, titulo: str, texto: str, erro: bool = False):
    top = ctk.CTkToplevel(master)
    top.title(titulo)
    top.geometry("420x180")
    top.resizable(False, False)
    top.transient(master.winfo_toplevel())
    top.grab_set()
    cor = tema.VERMELHO if erro else tema.AZUL
    painel(top).pack(fill="both", expand=True, padx=12, pady=12)
    inner = top.winfo_children()[-1]
    rotulo(inner, titulo, 16, True, cor).pack(anchor="w", padx=16, pady=(16, 8))
    ctk.CTkLabel(
        inner, text=texto, text_color=tema.TXT, wraplength=360, justify="left",
        font=ctk.CTkFont(family=tema.FONTE, size=13),
    ).pack(anchor="w", padx=16)
    botao(inner, "OK", top.destroy, "primario", width=100).pack(pady=16)
    top.wait_window()


def confirmar(master, titulo: str, texto: str) -> bool:
    resp = {"ok": False}
    top = ctk.CTkToplevel(master)
    top.title(titulo)
    top.geometry("440x190")
    top.resizable(False, False)
    top.transient(master.winfo_toplevel())
    top.grab_set()
    box = painel(top)
    box.pack(fill="both", expand=True, padx=12, pady=12)
    rotulo(box, titulo, 16, True).pack(anchor="w", padx=16, pady=(16, 8))
    ctk.CTkLabel(
        box, text=texto, text_color=tema.TXT, wraplength=380, justify="left",
        font=ctk.CTkFont(family=tema.FONTE, size=13),
    ).pack(anchor="w", padx=16)

    def sim():
        resp["ok"] = True
        top.destroy()

    linha = ctk.CTkFrame(box, fg_color="transparent")
    linha.pack(pady=16)
    botao(linha, "Cancelar", top.destroy, "secundario", width=110).pack(side="left", padx=6)
    botao(linha, "Confirmar", sim, "perigo", width=110).pack(side="left", padx=6)
    top.wait_window()
    return resp["ok"]


def tabela(master, colunas: list[tuple[str, int]], altura=18) -> ttk.Treeview:
    configurar_treeview()
    wrap = ctk.CTkFrame(master, fg_color="white")
    wrap.pack(fill="both", expand=True, padx=8, pady=8)
    ids = [c[0] for c in colunas]
    tree = ttk.Treeview(wrap, columns=ids, show="headings", style="Gestao.Treeview", height=altura)
    for cid, largura in colunas:
        tree.heading(cid, text=cid)
        tree.column(cid, width=largura, anchor="w")
    sy = ttk.Scrollbar(wrap, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=sy.set)
    tree.pack(side="left", fill="both", expand=True)
    sy.pack(side="right", fill="y")
    return tree


def preencher(tree: ttk.Treeview, linhas: list[tuple], iids: Optional[list] = None) -> None:
    tree.delete(*tree.get_children())
    for i, linha in enumerate(linhas):
        iid = str(iids[i]) if iids else str(i)
        tree.insert("", "end", iid=iid, values=linha)


def selecionado_id(tree: ttk.Treeview) -> Optional[int]:
    sel = tree.selection()
    if not sel:
        return None
    try:
        return int(sel[0])
    except ValueError:
        return None


class Formulario(ctk.CTkToplevel):
    def __init__(self, master, titulo: str, largura=560, altura=560):
        super().__init__(master)
        self.title(titulo)
        self.geometry(f"{largura}x{altura}")
        self.configure(fg_color=tema.BG_APP)
        self.transient(master.winfo_toplevel())
        self.grab_set()
        self.resultado = None
        self.campos: dict[str, ctk.CTkEntry | ctk.CTkComboBox | ctk.CTkTextbox] = {}
        self.corpo = ctk.CTkScrollableFrame(self, fg_color=tema.BG_PAINEL, corner_radius=12)
        self.corpo.pack(fill="both", expand=True, padx=14, pady=14)
        rotulo(self.corpo, titulo, 18, True).pack(anchor="w", padx=8, pady=(8, 12))

    def campo(self, chave: str, label: str, valor="", opcoes=None, senha=False, texto_longo=False):
        rotulo(self.corpo, label, 12).pack(anchor="w", padx=8, pady=(8, 2))
        if opcoes is not None:
            w = ctk.CTkComboBox(
                self.corpo, values=opcoes, fg_color="white", border_color=tema.BORDA,
                text_color=tema.TXT, dropdown_fg_color="white", height=34, width=480,
            )
            w.set(valor if valor in opcoes else (opcoes[0] if opcoes else ""))
        elif texto_longo:
            w = ctk.CTkTextbox(self.corpo, height=80, fg_color="white", text_color=tema.TXT, width=480)
            w.insert("1.0", valor or "")
        else:
            w = entrada(self.corpo, width=480, show="*" if senha else "")
            if valor not in (None, ""):
                w.insert(0, str(valor))
        w.pack(anchor="w", padx=8)
        self.campos[chave] = w
        return w

    def valor(self, chave: str) -> str:
        w = self.campos[chave]
        if isinstance(w, ctk.CTkTextbox):
            return w.get("1.0", "end").strip()
        return w.get().strip()

    def botoes(self, ao_salvar: Callable):
        linha = ctk.CTkFrame(self, fg_color="transparent")
        linha.pack(fill="x", padx=14, pady=(0, 14))
        botao(linha, "Cancelar", self.destroy, "secundario", width=120).pack(side="right", padx=6)
        botao(linha, "Salvar", ao_salvar, "primario", width=120).pack(side="right")
