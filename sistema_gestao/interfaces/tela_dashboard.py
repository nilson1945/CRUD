"""Dashboard com cartões, gráficos e lembretes do dia."""

from __future__ import annotations

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

import dashboard
import tema
from interfaces.componentes import card_kpi, painel, rotulo
from validacoes import formatar_data, formatar_moeda


class TelaDashboard(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color=tema.BG_CONTENT)
        self.app = app
        self.canvas_curso = None
        self.canvas_fin = None
        self._montar()

    def _montar(self):
        for w in self.winfo_children():
            w.destroy()
        dados = dashboard.cartoes()
        rotulo(self, "Dashboard", 22, True).pack(anchor="w", padx=20, pady=(16, 8))

        grade = ctk.CTkFrame(self, fg_color="transparent")
        grade.pack(fill="x", padx=12)
        for i in range(3):
            grade.grid_columnconfigure(i, weight=1)
        cards = [
            ("Funcionários", str(dados["funcionarios"]), "Cadastros ativos"),
            ("Clientes", str(dados["clientes"]), "Cadastros ativos"),
            ("Matrículas ativas", str(dados["matriculas_ativas"]), "Em andamento"),
            ("Cursos disponíveis", str(dados["cursos"]), "Catálogo ativo"),
            ("Mensalidades pendentes", str(dados["mensalidades_pendentes"]),
             f"Em atraso: {formatar_moeda(dados['valor_atraso'])}"),
            ("Recebido no mês", formatar_moeda(dados["recebido_mes"]),
             f"A receber: {formatar_moeda(dados['a_receber'])}"),
        ]
        for i, (t, v, s) in enumerate(cards):
            card_kpi(grade, t, v, s).grid(row=i // 3, column=i % 3, padx=8, pady=8, sticky="ew")

        meio = ctk.CTkFrame(self, fg_color="transparent")
        meio.pack(fill="both", expand=True, padx=12, pady=8)
        meio.grid_columnconfigure(0, weight=1)
        meio.grid_columnconfigure(1, weight=1)
        meio.grid_rowconfigure(0, weight=1)

        box_g = painel(meio)
        box_g.grid(row=0, column=0, sticky="nsew", padx=8, pady=4)
        rotulo(box_g, "Matrículas por curso", 15, True).pack(anchor="w", padx=12, pady=8)
        self._grafico_cursos(box_g)

        box_f = painel(meio)
        box_f.grid(row=0, column=1, sticky="nsew", padx=8, pady=4)
        rotulo(box_f, "Situação financeira", 15, True).pack(anchor="w", padx=12, pady=8)
        self._grafico_fin(box_f, dados)

        lem = painel(self)
        lem.pack(fill="x", padx=20, pady=(4, 16))
        rotulo(lem, "Lembretes do dia e atrasados", 15, True).pack(anchor="w", padx=14, pady=(10, 4))
        itens = []
        for l in dados["lembretes_atrasados"][:5]:
            itens.append(f"ATRASADO — {formatar_data(l['data'])} {l['horario'] or ''} · {l['titulo']}")
        for l in dados["lembretes_hoje"][:5]:
            itens.append(f"HOJE — {l['horario'] or ''} · {l['titulo']}")
        if not itens:
            itens = ["Nenhum lembrete pendente para hoje."]
        for txt in itens:
            rotulo(lem, txt, 13, cor=tema.TXT_SUAVE).pack(anchor="w", padx=14, pady=2)
        ctk.CTkLabel(lem, text=" ", height=8).pack()

    def recarregar(self):
        self._montar()

    def _grafico_cursos(self, parent):
        dados = dashboard.matriculas_por_curso()
        fig = Figure(figsize=(4.6, 2.6), dpi=100, facecolor="white")
        ax = fig.add_subplot(111)
        ax.set_facecolor("white")
        if dados:
            nomes = [n[:18] for n, _ in dados]
            vals = [v for _, v in dados]
            ax.barh(nomes[::-1], vals[::-1], color="#3B82C4")
        else:
            ax.text(0.5, 0.5, "Sem matrículas ainda", ha="center", va="center")
            ax.set_axis_off()
        ax.tick_params(colors="#4B5563", labelsize=8)
        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)

    def _grafico_fin(self, parent, dados):
        fig = Figure(figsize=(4.6, 2.6), dpi=100, facecolor="white")
        ax = fig.add_subplot(111)
        labels = ["Recebido", "A receber", "Atraso"]
        valores = [dados["recebido_mes"], dados["a_receber"], dados["valor_atraso"]]
        cores = ["#059669", "#3B82C4", "#DC2626"]
        if sum(valores) <= 0:
            ax.text(0.5, 0.5, "Sem movimento financeiro", ha="center", va="center")
            ax.set_axis_off()
        else:
            ax.bar(labels, valores, color=cores)
            ax.tick_params(colors="#4B5563", labelsize=8)
        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)
