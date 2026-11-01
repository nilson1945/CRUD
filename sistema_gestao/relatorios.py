"""Consultas administrativas e exportação para PDF e Excel."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Optional

from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from database import BASE_DIR, get_connection, obter_config
from financeiro import clientes_inadimplentes, recebimentos_por_mes
from validacoes import formatar_moeda

EXPORT_DIR = BASE_DIR / "backups"


def _periodo(ini: Optional[str], fim: Optional[str]) -> tuple[str, str]:
    return ini or "1900-01-01", fim or "9999-12-31"


def funcionarios(ini=None, fim=None) -> list[dict]:
    i, f = _periodo(ini, fim)
    with get_connection() as con:
        rows = con.execute(
            """
            SELECT id, nome, cpf, cargo, tipo_usuario, situacao, data_admissao
            FROM funcionarios
            WHERE date(criado_em) BETWEEN ? AND ?
            ORDER BY nome
            """,
            (i, f),
        ).fetchall()
        return [dict(r) for r in rows]


def clientes(ini=None, fim=None) -> list[dict]:
    i, f = _periodo(ini, fim)
    with get_connection() as con:
        rows = con.execute(
            """
            SELECT id, nome, cpf, telefone, cidade, data_cadastro, situacao
            FROM clientes
            WHERE data_cadastro BETWEEN ? AND ?
            ORDER BY nome
            """,
            (i, f),
        ).fetchall()
        return [dict(r) for r in rows]


def cursos_mais_procurados(ini=None, fim=None) -> list[dict]:
    i, f = _periodo(ini, fim)
    with get_connection() as con:
        rows = con.execute(
            """
            SELECT c.nome, c.categoria, COUNT(m.id) AS total
            FROM cursos c
            LEFT JOIN matriculas m ON m.curso_id=c.id AND m.data_matricula BETWEEN ? AND ?
            GROUP BY c.id
            ORDER BY total DESC, c.nome
            """,
            (i, f),
        ).fetchall()
        return [dict(r) for r in rows]


def matriculas_por_curso(ini=None, fim=None) -> list[dict]:
    return cursos_mais_procurados(ini, fim)


def matriculas_por_situacao(situacao: str, ini=None, fim=None) -> list[dict]:
    i, f = _periodo(ini, fim)
    with get_connection() as con:
        rows = con.execute(
            """
            SELECT m.numero_matricula, cl.nome AS cliente, c.nome AS curso,
                   m.data_matricula, m.valor_final, m.situacao
            FROM matriculas m
            JOIN clientes cl ON cl.id=m.cliente_id
            JOIN cursos c ON c.id=m.curso_id
            WHERE m.situacao=? AND m.data_matricula BETWEEN ? AND ?
            ORDER BY m.data_matricula DESC
            """,
            (situacao, i, f),
        ).fetchall()
        return [dict(r) for r in rows]


def recebimentos(ini=None, fim=None) -> list[dict]:
    i, f = _periodo(ini, fim)
    with get_connection() as con:
        rows = con.execute(
            """
            SELECT g.data_pagamento, cl.nome AS cliente, m.numero_matricula,
                   g.valor_pago, g.forma_pagamento
            FROM pagamentos g
            JOIN parcelas p ON p.id=g.parcela_id
            JOIN matriculas m ON m.id=g.matricula_id
            JOIN clientes cl ON cl.id=g.cliente_id
            WHERE p.situacao != 'cancelada' AND g.data_pagamento BETWEEN ? AND ?
            ORDER BY g.data_pagamento
            """,
            (i, f),
        ).fetchall()
        return [dict(r) for r in rows]


def mensalidades_atraso() -> list[dict]:
    hoje = date.today().isoformat()
    with get_connection() as con:
        rows = con.execute(
            """
            SELECT cl.nome AS cliente, m.numero_matricula, p.numero AS parcela,
                   p.data_vencimento, p.valor, p.situacao
            FROM parcelas p
            JOIN matriculas m ON m.id=p.matricula_id
            JOIN clientes cl ON cl.id=m.cliente_id
            WHERE p.situacao IN ('pendente','parcial','atrasada') AND p.data_vencimento < ?
            ORDER BY p.data_vencimento
            """,
            (hoje,),
        ).fetchall()
        return [dict(r) for r in rows]


def inadimplentes() -> list[dict]:
    return clientes_inadimplentes()


def historico_pagamentos(ini=None, fim=None) -> list[dict]:
    return recebimentos(ini, fim)


def receber_por_mes(ano: Optional[int] = None) -> list[dict]:
    return [{"mes": m, "total": t} for m, t in recebimentos_por_mes(ano)]


TIPOS = {
    "funcionarios": ("Funcionários cadastrados", funcionarios),
    "clientes": ("Clientes cadastrados", clientes),
    "cursos_procurados": ("Cursos mais procurados", cursos_mais_procurados),
    "matriculas_curso": ("Matrículas por curso", matriculas_por_curso),
    "matriculas_ativas": ("Matrículas ativas", lambda i, f: matriculas_por_situacao("Ativa", i, f)),
    "matriculas_canceladas": ("Matrículas canceladas", lambda i, f: matriculas_por_situacao("Cancelada", i, f)),
    "recebimentos": ("Recebimentos no período", recebimentos),
    "atraso": ("Mensalidades em atraso", lambda i, f: mensalidades_atraso()),
    "inadimplentes": ("Clientes inadimplentes", lambda i, f: inadimplentes()),
    "pagamentos": ("Histórico de pagamentos", historico_pagamentos),
}


def gerar(tipo: str, ini=None, fim=None) -> tuple[str, list[dict]]:
    if tipo not in TIPOS:
        raise ValueError("Tipo de relatório inválido.")
    titulo, fn = TIPOS[tipo]
    return titulo, fn(ini, fim)


def _linhas(registros: list[dict]) -> tuple[list[str], list[list[str]]]:
    if not registros:
        return ["Informação"], [["Nenhum registro encontrado."]]
    cols = list(registros[0].keys())
    body = []
    for r in registros:
        linha = []
        for c in cols:
            v = r.get(c)
            if isinstance(v, float) and ("valor" in c or "total" in c or "salario" in c or "atraso" in c):
                linha.append(formatar_moeda(v))
            else:
                linha.append("" if v is None else str(v))
        body.append(linha)
    return cols, body


def exportar_excel(titulo: str, registros: list[dict], destino: Optional[Path] = None) -> Path:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    destino = destino or EXPORT_DIR / f"relatorio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.title = titulo[:31]
    cols, body = _linhas(registros)
    ws.append(cols)
    for linha in body:
        ws.append(linha)
    wb.save(destino)
    return destino


def exportar_pdf(titulo: str, registros: list[dict], destino: Optional[Path] = None) -> Path:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    destino = destino or EXPORT_DIR / f"relatorio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    empresa = obter_config("nome_empresa", "Dimensão do Logus")
    doc = SimpleDocTemplate(str(destino), pagesize=landscape(A4), leftMargin=24, rightMargin=24)
    styles = getSampleStyleSheet()
    story = [
        Paragraph(empresa, styles["Title"]),
        Paragraph(titulo, styles["Heading2"]),
        Paragraph(datetime.now().strftime("Gerado em %d/%m/%Y %H:%M"), styles["Normal"]),
        Spacer(1, 12),
    ]
    cols, body = _linhas(registros)
    data = [cols] + body
    table = Table(data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4B5563")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#D1D5DB")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F4F6")]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    story.append(table)
    doc.build(story)
    return destino
