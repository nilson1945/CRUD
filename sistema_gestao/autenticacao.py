"""Login, hash de senhas (bcrypt) e controle de permissões."""

from __future__ import annotations

import json
from typing import Any, Optional

import bcrypt

from database import get_connection, registrar_acao

SENHA_ADMIN_INICIAL = "Lg#2026Adm!"
MODULOS = [
    "dashboard",
    "funcionarios",
    "clientes",
    "cursos",
    "matriculas",
    "financeiro",
    "lembretes",
    "relatorios",
    "configuracoes",
]


def hash_senha(senha: str) -> str:
    return bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verificar_senha(senha: str, senha_hash: str) -> bool:
    if not senha or not senha_hash:
        return False
    try:
        return bcrypt.checkpw(senha.encode("utf-8"), senha_hash.encode("utf-8"))
    except ValueError:
        return False


def autenticar(usuario: str, senha: str) -> Optional[dict[str, Any]]:
    usuario = (usuario or "").strip()
    with get_connection() as con:
        row = con.execute(
            """
            SELECT * FROM funcionarios
            WHERE (usuario = ? OR email = ?) AND situacao = 'ativo'
            """,
            (usuario, usuario),
        ).fetchone()
        if not row:
            return None
        if not verificar_senha(senha, row["senha_hash"] or ""):
            return None
        dados = dict(row)
        dados["permissoes"] = _parse_permissoes(dados.get("permissoes"), dados.get("tipo_usuario"))
        registrar_acao(dados["id"], "login", "funcionarios", dados["id"], f"Login de {usuario}")
        return dados


def alterar_senha(funcionario_id: int, senha_atual: str, senha_nova: str) -> None:
    if len(senha_nova) < 8:
        raise ValueError("A nova senha deve ter pelo menos 8 caracteres.")
    with get_connection() as con:
        row = con.execute(
            "SELECT senha_hash FROM funcionarios WHERE id=?", (funcionario_id,)
        ).fetchone()
        if not row or not verificar_senha(senha_atual, row["senha_hash"] or ""):
            raise ValueError("Senha atual incorreta.")
        novo = hash_senha(senha_nova)
        con.execute(
            "UPDATE funcionarios SET senha_hash=?, senha_provisoria=0 WHERE id=?",
            (novo, funcionario_id),
        )
        con.execute(
            "UPDATE usuarios SET senha_hash=? WHERE funcionario_id=?",
            (novo, funcionario_id),
        )
        con.commit()
    registrar_acao(funcionario_id, "alterar_senha", "funcionarios", funcionario_id)


def definir_senha_admin(funcionario_id: int, senha_nova: str, admin_id: int) -> None:
    if len(senha_nova) < 8:
        raise ValueError("A senha deve ter pelo menos 8 caracteres.")
    novo = hash_senha(senha_nova)
    with get_connection() as con:
        con.execute(
            "UPDATE funcionarios SET senha_hash=?, senha_provisoria=1 WHERE id=?",
            (novo, funcionario_id),
        )
        con.execute(
            "UPDATE usuarios SET senha_hash=? WHERE funcionario_id=?",
            (novo, funcionario_id),
        )
        con.commit()
    registrar_acao(admin_id, "redefinir_senha", "funcionarios", funcionario_id)


def tem_permissao(sessao: dict, modulo: str) -> bool:
    if not sessao:
        return False
    if sessao.get("tipo_usuario") == "administrador":
        return True
    return modulo in (sessao.get("permissoes") or [])


def eh_admin(sessao: dict) -> bool:
    return bool(sessao) and sessao.get("tipo_usuario") == "administrador"


def _parse_permissoes(raw: Any, tipo: Optional[str]) -> list[str]:
    from database import PERMISSOES_ADMIN, PERMISSOES_FUNCIONARIO

    if tipo == "administrador":
        return list(PERMISSOES_ADMIN)
    if not raw:
        return list(PERMISSOES_FUNCIONARIO)
    if isinstance(raw, list):
        return raw
    try:
        data = json.loads(raw)
        return data if isinstance(data, list) else list(PERMISSOES_FUNCIONARIO)
    except (json.JSONDecodeError, TypeError):
        return list(PERMISSOES_FUNCIONARIO)
