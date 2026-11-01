"""
Módulo de lembretes e compromissos — integrado à aplicação principal.

O arquivo original `lembretes/lembretes.py` cadastrava colaborador e cliente
em arquivos texto. Esse cadastro foi incorporado aos módulos de funcionários
e clientes; aqui ficam os compromissos, cobranças e avisos da empresa.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Optional

from database import get_connection, registrar_acao

CATEGORIAS = [
    "Compromisso",
    "Retorno de cliente",
    "Cobrança",
    "Vencimento de mensalidade",
    "Reunião",
    "Matrícula",
    "Outros",
]
PRIORIDADES = ["Baixa", "Média", "Alta"]


def listar(
    busca: str = "",
    somente_abertos: bool = False,
    data_ini: str = "",
    data_fim: str = "",
) -> list[dict]:
    sql = """
        SELECT l.*,
               f.nome AS funcionario_nome,
               cl.nome AS cliente_nome,
               m.numero_matricula
        FROM lembretes l
        LEFT JOIN funcionarios f ON f.id = l.funcionario_id
        LEFT JOIN clientes cl ON cl.id = l.cliente_id
        LEFT JOIN matriculas m ON m.id = l.matricula_id
        WHERE 1=1
    """
    params: list[Any] = []
    if somente_abertos:
        sql += " AND l.concluido=0"
    if busca.strip():
        like = f"%{busca.strip()}%"
        sql += " AND (l.titulo LIKE ? OR l.descricao LIKE ? OR cl.nome LIKE ?)"
        params.extend([like, like, like])
    if data_ini:
        sql += " AND l.data >= ?"
        params.append(data_ini)
    if data_fim:
        sql += " AND l.data <= ?"
        params.append(data_fim)
    sql += " ORDER BY l.concluido, l.data, l.horario"
    with get_connection() as con:
        return [dict(r) for r in con.execute(sql, params)]


def obter(lid: int) -> Optional[dict]:
    with get_connection() as con:
        row = con.execute("SELECT * FROM lembretes WHERE id=?", (lid,)).fetchone()
        return dict(row) if row else None


def salvar(dados: dict, usuario_logado: dict) -> int:
    if not (dados.get("titulo") or "").strip():
        raise ValueError("Informe o título do lembrete.")
    if not dados.get("data"):
        raise ValueError("Informe a data do lembrete.")
    agora = datetime.now().isoformat(timespec="seconds")
    valores = (
        dados["titulo"].strip(),
        dados.get("descricao"),
        dados["data"],
        dados.get("horario") or "09:00",
        dados.get("prioridade") or "Média",
        dados.get("categoria") or "Outros",
        dados.get("funcionario_id") or usuario_logado.get("id"),
        dados.get("cliente_id") or None,
        dados.get("matricula_id") or None,
        1 if dados.get("concluido") else 0,
    )
    with get_connection() as con:
        if dados.get("id"):
            con.execute(
                """
                UPDATE lembretes SET titulo=?, descricao=?, data=?, horario=?,
                    prioridade=?, categoria=?, funcionario_id=?, cliente_id=?,
                    matricula_id=?, concluido=?
                WHERE id=?
                """,
                valores + (dados["id"],),
            )
            lid = int(dados["id"])
            acao = "editar"
        else:
            cur = con.execute(
                """
                INSERT INTO lembretes (
                    titulo, descricao, data, horario, prioridade, categoria,
                    funcionario_id, cliente_id, matricula_id, concluido, criado_em
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                valores + (agora,),
            )
            lid = int(cur.lastrowid)
            acao = "cadastrar"
        con.commit()
    registrar_acao(usuario_logado["id"], acao, "lembretes", lid, dados["titulo"])
    return lid


def excluir(lid: int, usuario_logado: dict) -> None:
    with get_connection() as con:
        con.execute("DELETE FROM lembretes WHERE id=?", (lid,))
        con.commit()
    registrar_acao(usuario_logado["id"], "excluir", "lembretes", lid)


def concluir(lid: int, usuario_logado: dict, feito: bool = True) -> None:
    with get_connection() as con:
        con.execute("UPDATE lembretes SET concluido=? WHERE id=?", (1 if feito else 0, lid))
        con.commit()
    registrar_acao(usuario_logado["id"], "concluir" if feito else "reabrir", "lembretes", lid)


def do_dia() -> list[dict]:
    hoje = date.today().isoformat()
    return listar(somente_abertos=True, data_ini=hoje, data_fim=hoje)


def atrasados() -> list[dict]:
    ontem = (date.today() - timedelta(days=1)).isoformat()
    return listar(somente_abertos=True, data_fim=ontem)


def proximos(dias: int = 7) -> list[dict]:
    hoje = date.today().isoformat()
    fim = (date.today() + timedelta(days=dias)).isoformat()
    return listar(somente_abertos=True, data_ini=hoje, data_fim=fim)


def resumo_notificacoes() -> dict:
    return {
        "hoje": do_dia(),
        "atrasados": atrasados(),
        "proximos": proximos(7),
    }
