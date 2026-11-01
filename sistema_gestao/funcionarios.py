"""Regras de negócio do cadastro de funcionários."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Optional

from autenticacao import hash_senha
from database import (
    PERMISSOES_ADMIN,
    PERMISSOES_FUNCIONARIO,
    get_connection,
    registrar_acao,
    salvar_config,
)
from validacoes import campo_obrigatorio, formatar_cpf, validar_cpf, validar_email


def listar(busca: str = "", incluir_inativos: bool = True) -> list[dict]:
    sql = "SELECT * FROM funcionarios WHERE 1=1"
    params: list[Any] = []
    if not incluir_inativos:
        sql += " AND situacao='ativo'"
    if busca.strip():
        sql += " AND (nome LIKE ? OR cpf LIKE ? OR usuario LIKE ?)"
        like = f"%{busca.strip()}%"
        params.extend([like, like, like])
    sql += " ORDER BY nome"
    with get_connection() as con:
        return [dict(r) for r in con.execute(sql, params)]


def obter(fid: int) -> Optional[dict]:
    with get_connection() as con:
        row = con.execute("SELECT * FROM funcionarios WHERE id=?", (fid,)).fetchone()
        return dict(row) if row else None


def salvar(dados: dict, usuario_logado: dict) -> int:
    if usuario_logado.get("tipo_usuario") != "administrador":
        raise PermissionError("Somente o administrador pode cadastrar funcionários.")
    erro = campo_obrigatorio(dados.get("nome", ""), "nome")
    if erro:
        raise ValueError(erro)
    if not dados.get("usuario"):
        raise ValueError("Informe o usuário de acesso.")
    cpf = (dados.get("cpf") or "").strip()
    if cpf:
        if not validar_cpf(cpf):
            raise ValueError("CPF inválido.")
        cpf = formatar_cpf(cpf)
    email = (dados.get("email") or "").strip()
    if email and not validar_email(email):
        raise ValueError("E-mail inválido.")
    tipo = dados.get("tipo_usuario") or "funcionario"
    perms = dados.get("permissoes")
    if tipo == "administrador":
        perms = PERMISSOES_ADMIN
    elif not perms:
        perms = PERMISSOES_FUNCIONARIO

    agora = datetime.now().isoformat(timespec="seconds")
    with get_connection() as con:
        if cpf:
            dup = con.execute(
                "SELECT id FROM funcionarios WHERE cpf=? AND id!=?",
                (cpf, dados.get("id") or 0),
            ).fetchone()
            if dup:
                raise ValueError("Já existe funcionário com este CPF.")
        dup_u = con.execute(
            "SELECT id FROM funcionarios WHERE usuario=? AND id!=?",
            (dados["usuario"], dados.get("id") or 0),
        ).fetchone()
        if dup_u:
            raise ValueError("Este nome de usuário já está em uso.")

        if dados.get("id"):
            con.execute(
                """
                UPDATE funcionarios SET nome=?, cpf=?, rg=?, data_nascimento=?,
                    telefone=?, email=?, endereco=?, cargo=?, data_admissao=?,
                    salario=?, tipo_usuario=?, situacao=?, usuario=?, permissoes=?
                WHERE id=?
                """,
                (
                    dados["nome"].strip(), cpf or None, dados.get("rg"),
                    dados.get("data_nascimento"), dados.get("telefone"),
                    email or None, dados.get("endereco"), dados.get("cargo"),
                    dados.get("data_admissao"), dados.get("salario"),
                    tipo, dados.get("situacao") or "ativo", dados["usuario"],
                    json.dumps(perms), dados["id"],
                ),
            )
            con.execute(
                "UPDATE usuarios SET usuario=?, tipo=?, ativo=? WHERE funcionario_id=?",
                (
                    dados["usuario"], tipo,
                    1 if (dados.get("situacao") or "ativo") == "ativo" else 0,
                    dados["id"],
                ),
            )
            if dados.get("senha"):
                sh = hash_senha(dados["senha"])
                con.execute(
                    "UPDATE funcionarios SET senha_hash=?, senha_provisoria=1 WHERE id=?",
                    (sh, dados["id"]),
                )
                con.execute(
                    "UPDATE usuarios SET senha_hash=? WHERE funcionario_id=?",
                    (sh, dados["id"]),
                )
            con.commit()
            registrar_acao(usuario_logado["id"], "editar", "funcionarios", dados["id"], dados["nome"])
            return int(dados["id"])

        if not dados.get("senha"):
            raise ValueError("Informe a senha de acesso.")
        sh = hash_senha(dados["senha"])
        cur = con.execute(
            """
            INSERT INTO funcionarios (
                nome, cpf, rg, data_nascimento, telefone, email, endereco, cargo,
                data_admissao, salario, senha_hash, tipo_usuario, situacao, usuario,
                senha_provisoria, permissoes, criado_em
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
            """,
            (
                dados["nome"].strip(), cpf or None, dados.get("rg"),
                dados.get("data_nascimento"), dados.get("telefone"),
                email or None, dados.get("endereco"), dados.get("cargo"),
                dados.get("data_admissao"), dados.get("salario"), sh, tipo,
                dados.get("situacao") or "ativo", dados["usuario"],
                json.dumps(perms), agora,
            ),
        )
        fid = cur.lastrowid
        con.execute(
            """
            INSERT INTO usuarios (funcionario_id, usuario, senha_hash, tipo, ativo)
            VALUES (?, ?, ?, ?, 1)
            """,
            (fid, dados["usuario"], sh, tipo),
        )
        con.commit()
        registrar_acao(usuario_logado["id"], "cadastrar", "funcionarios", fid, dados["nome"])
        return int(fid)


def primeiro_acesso_pendente() -> bool:
    """True enquanto nenhum administrador tiver senha definitiva configurada."""
    with get_connection() as con:
        row = con.execute(
            """
            SELECT COUNT(*) c FROM funcionarios
            WHERE tipo_usuario='administrador' AND situacao='ativo' AND senha_provisoria=0
            """
        ).fetchone()
        return row["c"] == 0


def salvar_empresa(dados: dict) -> None:
    """Grava os dados cadastrais da empresa nas configurações do sistema."""
    nome = (dados.get("nome_empresa") or "").strip()
    if not nome:
        raise ValueError("Informe o nome da empresa.")
    email = (dados.get("empresa_email") or "").strip()
    if email and not validar_email(email):
        raise ValueError("E-mail da empresa inválido.")
    valores = {
        "nome_empresa": nome,
        "empresa_cnpj": (dados.get("empresa_cnpj") or "").strip(),
        "empresa_telefone": (dados.get("empresa_telefone") or "").strip(),
        "empresa_email": email,
        "empresa_endereco": (dados.get("empresa_endereco") or "").strip(),
        "empresa_cidade": (dados.get("empresa_cidade") or "").strip(),
        "empresa_estado": (dados.get("empresa_estado") or "").strip().upper(),
    }
    for chave, valor in valores.items():
        salvar_config(chave, valor)


def criar_usuario_inicial(dados: dict) -> int:
    """Cadastro de primeiro acesso: cria o usuário administrador definitivo."""
    if not primeiro_acesso_pendente():
        raise PermissionError(
            "O sistema já possui administrador configurado. "
            "Procure o administrador para criar o seu acesso."
        )
    nome = (dados.get("nome") or "").strip()
    usuario = (dados.get("usuario") or "").strip()
    senha = dados.get("senha") or ""
    if not nome:
        raise ValueError("Informe o nome do usuário.")
    if not usuario:
        raise ValueError("Informe o usuário de acesso.")
    if len(senha) < 8:
        raise ValueError("A senha deve ter pelo menos 8 caracteres.")

    agora = datetime.now().isoformat(timespec="seconds")
    sh = hash_senha(senha)
    with get_connection() as con:
        ocupado = con.execute(
            "SELECT id FROM funcionarios WHERE usuario=?", (usuario,)
        ).fetchone()
        padrao = con.execute(
            "SELECT id FROM funcionarios WHERE usuario='admin'"
        ).fetchone()
        alvo = padrao["id"] if padrao else None
        if ocupado and ocupado["id"] != alvo:
            raise ValueError("Este nome de usuário já está em uso.")
        if alvo:
            con.execute(
                """
                UPDATE funcionarios SET nome=?, usuario=?, senha_hash=?, senha_provisoria=0,
                    tipo_usuario='administrador', situacao='ativo', permissoes=?
                WHERE id=?
                """,
                (nome, usuario, sh, json.dumps(PERMISSOES_ADMIN), alvo),
            )
            con.execute(
                "UPDATE usuarios SET usuario=?, senha_hash=?, tipo='administrador', ativo=1 "
                "WHERE funcionario_id=?",
                (usuario, sh, alvo),
            )
            fid = alvo
        else:
            cur = con.execute(
                """
                INSERT INTO funcionarios (
                    nome, tipo_usuario, situacao, usuario, senha_hash,
                    senha_provisoria, permissoes, data_admissao, criado_em
                ) VALUES (?, 'administrador', 'ativo', ?, ?, 0, ?, ?, ?)
                """,
                (
                    nome, usuario, sh, json.dumps(PERMISSOES_ADMIN),
                    datetime.now().date().isoformat(), agora,
                ),
            )
            fid = cur.lastrowid
            con.execute(
                "INSERT INTO usuarios (funcionario_id, usuario, senha_hash, tipo, ativo) "
                "VALUES (?, ?, ?, 'administrador', 1)",
                (fid, usuario, sh),
            )
        con.commit()
    registrar_acao(fid, "primeiro_acesso", "funcionarios", fid, nome)
    return int(fid)


def inativar(fid: int, usuario_logado: dict) -> None:
    if usuario_logado.get("tipo_usuario") != "administrador":
        raise PermissionError("Somente o administrador pode excluir ou inativar funcionários.")
    if fid == usuario_logado.get("id"):
        raise ValueError("Você não pode inativar o próprio usuário.")
    with get_connection() as con:
        con.execute("UPDATE funcionarios SET situacao='inativo' WHERE id=?", (fid,))
        con.execute("UPDATE usuarios SET ativo=0 WHERE funcionario_id=?", (fid,))
        con.commit()
    registrar_acao(usuario_logado["id"], "inativar", "funcionarios", fid)


def excluir(fid: int, usuario_logado: dict) -> None:
    if usuario_logado.get("tipo_usuario") != "administrador":
        raise PermissionError("Somente o administrador pode excluir funcionários.")
    if fid == usuario_logado.get("id"):
        raise ValueError("Você não pode excluir o próprio usuário.")
    with get_connection() as con:
        usados = con.execute(
            "SELECT COUNT(*) n FROM matriculas WHERE funcionario_id=?", (fid,)
        ).fetchone()["n"]
        if usados:
            raise ValueError(
                "Este funcionário possui matrículas vinculadas. Use inativar em vez de excluir."
            )
        con.execute("DELETE FROM usuarios WHERE funcionario_id=?", (fid,))
        con.execute("UPDATE lembretes SET funcionario_id=NULL WHERE funcionario_id=?", (fid,))
        con.execute("DELETE FROM funcionarios WHERE id=?", (fid,))
        con.commit()
    registrar_acao(usuario_logado["id"], "excluir", "funcionarios", fid)
