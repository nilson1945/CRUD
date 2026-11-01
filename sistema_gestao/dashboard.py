"""Indicadores da tela inicial."""

from __future__ import annotations

from database import get_connection
from financeiro import indicadores
from lembrete import resumo_notificacoes


def cartoes() -> dict:
    with get_connection() as con:
        funcionarios = con.execute(
            "SELECT COUNT(*) n FROM funcionarios WHERE situacao='ativo'"
        ).fetchone()["n"]
        clientes = con.execute(
            "SELECT COUNT(*) n FROM clientes WHERE situacao='ativo'"
        ).fetchone()["n"]
        matriculas = con.execute(
            "SELECT COUNT(*) n FROM matriculas WHERE situacao='Ativa'"
        ).fetchone()["n"]
        cursos = con.execute(
            "SELECT COUNT(*) n FROM cursos WHERE situacao='ativo'"
        ).fetchone()["n"]
    fin = indicadores()
    notes = resumo_notificacoes()
    return {
        "funcionarios": funcionarios,
        "clientes": clientes,
        "matriculas_ativas": matriculas,
        "cursos": cursos,
        "mensalidades_pendentes": fin["pendentes_qtd"],
        "valor_atraso": fin["atraso"],
        "recebido_mes": fin["recebido_mes"],
        "a_receber": fin["a_receber"],
        "lembretes_hoje": notes["hoje"],
        "lembretes_atrasados": notes["atrasados"],
        "lembretes_proximos": notes["proximos"],
    }


def matriculas_por_curso() -> list[tuple[str, int]]:
    with get_connection() as con:
        rows = con.execute(
            """
            SELECT c.nome, COUNT(m.id) n
            FROM cursos c
            LEFT JOIN matriculas m ON m.curso_id = c.id AND m.situacao IN ('Ativa','Pré-matrícula','Trancada')
            GROUP BY c.id
            HAVING n > 0
            ORDER BY n DESC
            LIMIT 10
            """
        ).fetchall()
        return [(r["nome"], int(r["n"])) for r in rows]


def situacao_financeira_resumo() -> dict:
    return indicadores()
