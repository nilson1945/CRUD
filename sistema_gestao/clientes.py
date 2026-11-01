"""Cadastro de clientes e consultas de histórico."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from database import get_connection, registrar_acao
from validacoes import campo_obrigatorio, formatar_cpf, somente_digitos, validar_cpf, validar_email


def listar(busca: str = "", incluir_inativos: bool = True) -> list[dict]:
    sql = "SELECT * FROM clientes WHERE 1=1"
    params: list[Any] = []
    if not incluir_inativos:
        sql += " AND situacao='ativo'"
    if busca.strip():
        like = f"%{busca.strip()}%"
        dig = f"%{somente_digitos(busca)}%"
        sql += " AND (nome LIKE ? OR cpf LIKE ? OR telefone LIKE ? OR whatsapp LIKE ? OR replace(replace(replace(cpf,'.',''),'-',''),' ','') LIKE ?)"
        params.extend([like, like, like, like, dig])
    sql += " ORDER BY nome"
    with get_connection() as con:
        return [dict(r) for r in con.execute(sql, params)]


def obter(cid: int) -> Optional[dict]:
    with get_connection() as con:
        row = con.execute("SELECT * FROM clientes WHERE id=?", (cid,)).fetchone()
        return dict(row) if row else None


def salvar(dados: dict, usuario_logado: dict) -> int:
    erro = campo_obrigatorio(dados.get("nome", ""), "nome")
    if erro:
        raise ValueError(erro)
    cpf = (dados.get("cpf") or "").strip()
    if cpf:
        if not validar_cpf(cpf):
            raise ValueError("CPF inválido.")
        cpf = formatar_cpf(cpf)
    email = (dados.get("email") or "").strip()
    if email and not validar_email(email):
        raise ValueError("E-mail inválido.")
    hoje = datetime.now().date().isoformat()
    situacao = dados.get("situacao") or "ativo"
    base = (
        dados["nome"].strip(),
        cpf or None,
        dados.get("rg"),
        dados.get("data_nascimento"),
        dados.get("telefone"),
        dados.get("whatsapp") or dados.get("telefone"),
        email or None,
        dados.get("cep"),
        dados.get("endereco"),
        dados.get("numero"),
        dados.get("bairro"),
        dados.get("cidade"),
        dados.get("estado"),
        dados.get("observacoes"),
        situacao,
    )
    with get_connection() as con:
        if cpf:
            dup = con.execute(
                "SELECT id, nome FROM clientes WHERE cpf=? AND id!=?",
                (cpf, dados.get("id") or 0),
            ).fetchone()
            if dup:
                raise ValueError(f"Já existe cliente com este CPF: {dup['nome']}.")
        if dados.get("id"):
            con.execute(
                """
                UPDATE clientes SET nome=?, cpf=?, rg=?, data_nascimento=?, telefone=?,
                    whatsapp=?, email=?, cep=?, endereco=?, numero=?, bairro=?, cidade=?,
                    estado=?, observacoes=?, situacao=?
                WHERE id=?
                """,
                base + (dados["id"],),
            )
            cid = int(dados["id"])
            acao = "editar"
        else:
            cur = con.execute(
                """
                INSERT INTO clientes (
                    nome, cpf, rg, data_nascimento, telefone, whatsapp, email, cep,
                    endereco, numero, bairro, cidade, estado, data_cadastro, observacoes, situacao
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                base[:13] + (hoje,) + base[13:],
            )
            cid = int(cur.lastrowid)
            acao = "cadastrar"
        con.commit()
    registrar_acao(usuario_logado["id"], acao, "clientes", cid, dados["nome"])
    return cid


def inativar(cid: int, usuario_logado: dict) -> None:
    with get_connection() as con:
        con.execute("UPDATE clientes SET situacao='inativo' WHERE id=?", (cid,))
        con.commit()
    registrar_acao(usuario_logado["id"], "inativar", "clientes", cid)


def excluir(cid: int, usuario_logado: dict) -> None:
    with get_connection() as con:
        mats = con.execute(
            "SELECT COUNT(*) n FROM matriculas WHERE cliente_id=?", (cid,)
        ).fetchone()["n"]
        if mats:
            raise ValueError(
                "Este cliente possui matrículas. Use inativar para preservar o histórico."
            )
        con.execute("DELETE FROM lembretes WHERE cliente_id=?", (cid,))
        con.execute("DELETE FROM clientes WHERE id=?", (cid,))
        con.commit()
    registrar_acao(usuario_logado["id"], "excluir", "clientes", cid)


def historico_matriculas(cid: int) -> list[dict]:
    with get_connection() as con:
        rows = con.execute(
            """
            SELECT m.*, c.nome AS curso_nome
            FROM matriculas m JOIN cursos c ON c.id = m.curso_id
            WHERE m.cliente_id=? ORDER BY m.data_matricula DESC
            """,
            (cid,),
        ).fetchall()
        return [dict(r) for r in rows]


def historico_pagamentos(cid: int) -> list[dict]:
    with get_connection() as con:
        rows = con.execute(
            """
            SELECT p.*, c.nome AS curso_nome, m.numero_matricula
            FROM pagamentos p
            JOIN matriculas m ON m.id = p.matricula_id
            JOIN cursos c ON c.id = m.curso_id
            WHERE p.cliente_id=? ORDER BY p.data_pagamento DESC
            """,
            (cid,),
        ).fetchall()
        return [dict(r) for r in rows]


def historico_lembretes(cid: int) -> list[dict]:
    with get_connection() as con:
        rows = con.execute(
            "SELECT * FROM lembretes WHERE cliente_id=? ORDER BY data DESC, horario DESC",
            (cid,),
        ).fetchall()
        return [dict(r) for r in rows]
