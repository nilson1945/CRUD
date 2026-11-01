"""Catálogo de cursos técnicos e preparatórios."""

from __future__ import annotations

from typing import Any, Optional

from database import get_connection, registrar_acao
from validacoes import campo_obrigatorio, parse_moeda


def listar(busca: str = "", categoria: str = "", apenas_ativos: bool = False) -> list[dict]:
    sql = "SELECT * FROM cursos WHERE 1=1"
    params: list[Any] = []
    if apenas_ativos:
        sql += " AND situacao='ativo'"
    if categoria:
        sql += " AND categoria=?"
        params.append(categoria)
    if busca.strip():
        sql += " AND (nome LIKE ? OR modalidade LIKE ?)"
        like = f"%{busca.strip()}%"
        params.extend([like, like])
    sql += " ORDER BY categoria, nome"
    with get_connection() as con:
        return [dict(r) for r in con.execute(sql, params)]


def obter(curso_id: int) -> Optional[dict]:
    with get_connection() as con:
        row = con.execute("SELECT * FROM cursos WHERE id=?", (curso_id,)).fetchone()
        return dict(row) if row else None


def salvar(dados: dict, usuario_logado: dict) -> int:
    erro = campo_obrigatorio(dados.get("nome", ""), "nome")
    if erro:
        raise ValueError(erro)
    venda = dados.get("valor_venda")
    if isinstance(venda, str):
        venda = parse_moeda(venda)
    if venda is None:
        raise ValueError("Informe o valor de venda.")
    with get_connection() as con:
        valores = (
            dados["nome"].strip(),
            dados.get("categoria") or "Curso Técnico",
            dados.get("modalidade"),
            dados.get("valor_minimo") or 0,
            dados.get("valor_maximo") or 0,
            float(venda),
            dados.get("duracao_meses") or 12,
            dados.get("descricao"),
            dados.get("situacao") or "ativo",
        )
        if dados.get("id"):
            con.execute(
                """
                UPDATE cursos SET nome=?, categoria=?, modalidade=?, valor_minimo=?,
                    valor_maximo=?, valor_venda=?, duracao_meses=?, descricao=?, situacao=?
                WHERE id=?
                """,
                valores + (dados["id"],),
            )
            cid = int(dados["id"])
            acao = "editar"
        else:
            cur = con.execute(
                """
                INSERT INTO cursos (nome, categoria, modalidade, valor_minimo, valor_maximo,
                    valor_venda, duracao_meses, descricao, situacao)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                valores,
            )
            cid = int(cur.lastrowid)
            acao = "cadastrar"
        con.commit()
    registrar_acao(usuario_logado["id"], acao, "cursos", cid, dados["nome"])
    return cid


def inativar(curso_id: int, usuario_logado: dict) -> None:
    with get_connection() as con:
        con.execute("UPDATE cursos SET situacao='inativo' WHERE id=?", (curso_id,))
        con.commit()
    registrar_acao(usuario_logado["id"], "inativar", "cursos", curso_id)


def excluir(curso_id: int, usuario_logado: dict) -> None:
    with get_connection() as con:
        n = con.execute(
            "SELECT COUNT(*) n FROM matriculas WHERE curso_id=?", (curso_id,)
        ).fetchone()["n"]
        if n:
            raise ValueError("Curso possui matrículas. Inative-o para manter o histórico.")
        con.execute("DELETE FROM cursos WHERE id=?", (curso_id,))
        con.commit()
    registrar_acao(usuario_logado["id"], "excluir", "cursos", curso_id)
