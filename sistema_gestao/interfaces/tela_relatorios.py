"""Relatórios com filtro de período e exportação PDF/Excel."""

from __future__ import annotations

from datetime import date
from tkinter import filedialog

import customtkinter as ctk

import relatorios
import tema
from interfaces.componentes import botao, entrada, mensagem, painel, preencher, rotulo, tabela
from validacoes import formatar_moeda, parse_data


NOMES = {
    "funcionarios": "Funcionários cadastrados",
    "clientes": "Clientes cadastrados",
    "cursos_procurados": "Cursos mais procurados",
    "matriculas_curso": "Matrículas por curso",
    "matriculas_ativas": "Matrículas ativas",
    "matriculas_canceladas": "Matrículas canceladas",
    "recebimentos": "Recebimentos por período",
    "atraso": "Mensalidades em atraso",
    "inadimplentes": "Clientes inadimplentes",
    "pagamentos": "Histórico de pagamentos",
}


class TelaRelatorios(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color=tema.BG_CONTENT)
        self.app = app
        self.registros: list[dict] = []
        self.titulo = ""
        topo = painel(self)
        topo.pack(fill="x", padx=16, pady=16)
        rotulo(topo, "Relatórios", 20, True).pack(anchor="w", padx=16, pady=(12, 4))

        linha = ctk.CTkFrame(topo, fg_color="transparent")
        linha.pack(fill="x", padx=12, pady=8)
        rotulo(linha, "Tipo", 12).pack(side="left", padx=4)
        self.tipo = ctk.CTkComboBox(
            linha, values=list(NOMES.values()), width=260,
            fg_color="white", text_color=tema.TXT,
        )
        self.tipo.set(NOMES["clientes"])
        self.tipo.pack(side="left", padx=6)
        rotulo(linha, "De", 12).pack(side="left")
        self.ini = entrada(linha, width=110, placeholder_text="DD/MM/AAAA")
        self.ini.pack(side="left", padx=4)
        rotulo(linha, "Até", 12).pack(side="left")
        self.fim = entrada(linha, width=110, placeholder_text="DD/MM/AAAA")
        self.fim.pack(side="left", padx=4)
        botao(linha, "Gerar", self._gerar, width=100).pack(side="left", padx=6)
        botao(linha, "Excel", self._excel, "secundario", width=90).pack(side="left", padx=4)
        botao(linha, "PDF", self._pdf, "secundario", width=90).pack(side="left", padx=4)

        self.tree = tabela(self, [("Coluna 1", 200), ("Coluna 2", 200), ("Coluna 3", 200)], 16)

    def recarregar(self):
        pass

    def _chave(self) -> str:
        nome = self.tipo.get()
        for k, v in NOMES.items():
            if v == nome:
                return k
        return "clientes"

    def _gerar(self):
        ini = parse_data(self.ini.get()) if self.ini.get().strip() else None
        fim = parse_data(self.fim.get()) if self.fim.get().strip() else None
        self.titulo, self.registros = relatorios.gerar(self._chave(), ini, fim)
        self.tree.destroy()
        if self.registros:
            cols = list(self.registros[0].keys())
        else:
            cols = ["resultado"]
            self.registros = [{"resultado": "Nenhum registro no filtro informado."}]
        parent = self.tree.master if hasattr(self.tree, "master") else self
        # recria tabela
        wrap = [w for w in self.winfo_children() if isinstance(w, ctk.CTkFrame)]
        for w in list(self.winfo_children())[1:]:
            w.destroy()
        self.tree = tabela(self, [(c, max(90, 780 // max(len(cols), 1))) for c in cols], 16)
        linhas, iids = [], []
        for i, r in enumerate(self.registros):
            linha = []
            for c in cols:
                v = r.get(c)
                if isinstance(v, float):
                    linha.append(formatar_moeda(v) if any(x in c for x in ("valor", "total", "atraso")) else f"{v:.2f}")
                else:
                    linha.append("" if v is None else str(v))
            linhas.append(tuple(linha))
            iids.append(i)
        preencher(self.tree, linhas, iids)
        mensagem(self, "Relatório", f"{self.titulo}: {len(self.registros)} linha(s).")

    def _excel(self):
        if not self.registros:
            self._gerar()
        caminho = filedialog.asksaveasfilename(
            defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")]
        )
        if not caminho:
            return
        dest = relatorios.exportar_excel(self.titulo or "Relatório", self.registros)
        dest.replace(caminho) if False else None
        from pathlib import Path
        import shutil
        shutil.copy2(dest, caminho)
        mensagem(self, "Exportação", f"Arquivo Excel salvo em:\n{caminho}")

    def _pdf(self):
        if not self.registros:
            self._gerar()
        caminho = filedialog.asksaveasfilename(
            defaultextension=".pdf", filetypes=[("PDF", "*.pdf")]
        )
        if not caminho:
            return
        dest = relatorios.exportar_pdf(self.titulo or "Relatório", self.registros)
        import shutil
        shutil.copy2(dest, caminho)
        mensagem(self, "Exportação", f"Arquivo PDF salvo em:\n{caminho}")
