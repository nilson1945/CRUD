"""Matrículas: vínculo cliente-curso com valor congelado na contratação."""

from __future__ import annotations

from calendar import monthrange
from datetime import date, datetime
from typing import Any, Optional

from database import get_connection, transacao, registrar_acao
from validacoes import parse_moeda

SITUACOES = ["Pré-matrícula", "Ativa", "Concluída", "Cancelada", "Trancada"]
FORMAS = [
    "Dinheiro", "PIX", "Cartão de crédito", "Cartão de débito",
    "Boleto", "Transferência bancária",
]


def _proximo_numero(con) -> str:
    ano = datetime.now().year
    row = con.execute(
        "SELECT COUNT(*) n FROM matriculas WHERE numero_matricula LIKE ?",
        (f"MAT-{ano}-%",),
    ).fetchone()
    return f"MAT-{ano}-{int(row['n']) + 1:04d}"


def listar(busca: str = "", situacao: str = "") -> list[dict]:
    sql = """
        SELECT m.*, cl.nome AS cliente_nome, c.nome AS curso_nome
        FROM matriculas m
        JOIN clientes cl ON cl.id = m.cliente_id
        JOIN cursos c ON c.id = m.curso_id
        WHERE 1=1
    """
    params: list[Any] = []
    if situacao:
        sql += " AND m.situacao=?"
        params.append(situacao)
    if busca.strip():
        like = f"%{busca.strip()}%"
        sql += " AND (cl.nome LIKE ? OR c.nome LIKE ? OR m.numero_matricula LIKE ?)"
        params.extend([like, like, like])
    sql += " ORDER BY m.id DESC"
    with get_connection() as con:
        return [dict(r) for r in con.execute(sql, params)]


def obter(mid: int) -> Optional[dict]:
    with get_connection() as con:
        row = con.execute(
            """
            SELECT m.*, cl.nome AS cliente_nome, c.nome AS curso_nome
            FROM matriculas m
            JOIN clientes cl ON cl.id = m.cliente_id
            JOIN cursos c ON c.id = m.curso_id
            WHERE m.id=?
            """,
            (mid,),
        ).fetchone()
        return dict(row) if row else None


def salvar(dados: dict, usuario_logado: dict) -> int:
    if not dados.get("cliente_id") or not dados.get("curso_id"):
        raise ValueError("Selecione o cliente e o curso.")
    valor_original = dados.get("valor_original")
    if isinstance(valor_original, str):
        valor_original = parse_moeda(valor_original)
    desconto = dados.get("desconto") or 0
    if isinstance(desconto, str):
        desconto = parse_moeda(desconto) or 0
    valor_final = dados.get("valor_final")
    if isinstance(valor_final, str):
        valor_final = parse_moeda(valor_final)
    if valor_original is None:
        raise ValueError("Informe o valor original.")
    if valor_final is None:
        valor_final = round(float(valor_original) - float(desconto), 2)
    if valor_final < 0:
        raise ValueError("O valor final não pode ser negativo.")
    qtd = int(dados.get("qtd_parcelas") or 1)
    if qtd < 1:
        raise ValueError("A quantidade de parcelas deve ser pelo menos 1.")
    valor_parcela = round(float(valor_final) / qtd, 2)
    if dados.get("valor_parcela"):
        vp = dados["valor_parcela"]
        valor_parcela = parse_moeda(vp) if isinstance(vp, str) else float(vp)

    data_mat = dados.get("data_matricula") or date.today().isoformat()
    situacao = dados.get("situacao") or "Ativa"
    if situacao not in SITUACOES:
        raise ValueError("Situação de matrícula inválida.")

    with transacao() as con:
        if dados.get("id"):
            atual = con.execute(
                "SELECT valor_original, valor_final FROM matriculas WHERE id=?",
                (dados["id"],),
            ).fetchone()
            if not atual:
                raise ValueError("Matrícula não encontrada.")
            # preço contratado não muda automaticamente; só se o usuário informar
            con.execute(
                """
                UPDATE matriculas SET cliente_id=?, curso_id=?, data_matricula=?,
                    data_inicio=?, data_termino=?, desconto=?, valor_final=?,
                    qtd_parcelas=?, valor_parcela=?, dia_vencimento=?,
                    forma_pagamento=?, observacoes=?, situacao=?
                WHERE id=?
                """,
                (
                    dados["cliente_id"], dados["curso_id"], data_mat,
                    dados.get("data_inicio"), dados.get("data_termino"),
                    float(desconto), float(valor_final), qtd, valor_parcela,
                    dados.get("dia_vencimento"), dados.get("forma_pagamento"),
                    dados.get("observacoes"), situacao, dados["id"],
                ),
            )
            mid = int(dados["id"])
            if situacao == "Cancelada":
                con.execute(
                    "UPDATE parcelas SET situacao='cancelada' WHERE matricula_id=? AND situacao IN ('pendente','parcial','atrasada')",
                    (mid,),
                )
            acao = "editar"
        else:
            numero = _proximo_numero(con)
            cur = con.execute(
                """
                INSERT INTO matriculas (
                    numero_matricula, cliente_id, curso_id, data_matricula, data_inicio,
                    data_termino, valor_original, desconto, valor_final, qtd_parcelas,
                    valor_parcela, dia_vencimento, forma_pagamento, observacoes, situacao,
                    funcionario_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    numero, dados["cliente_id"], dados["curso_id"], data_mat,
                    dados.get("data_inicio"), dados.get("data_termino"),
                    float(valor_original), float(desconto), float(valor_final),
                    qtd, valor_parcela, dados.get("dia_vencimento"),
                    dados.get("forma_pagamento"), dados.get("observacoes"),
                    situacao, usuario_logado.get("id"),
                ),
            )
            mid = int(cur.lastrowid)
            _gerar_parcelas_con(
                con, mid, qtd, float(valor_final),
                dados.get("data_inicio") or data_mat,
                int(dados.get("dia_vencimento") or 10),
            )
            acao = "cadastrar"
        # não gera parcelas de novo na edição para não duplicar
    registrar_acao(usuario_logado["id"], acao, "matriculas", mid, str(mid))
    return mid


def _somar_meses(base: date, meses: int, dia: int) -> date:
    mes = base.month - 1 + meses
    ano = base.year + mes // 12
    mes = mes % 12 + 1
    dia = min(dia, monthrange(ano, mes)[1])
    return date(ano, mes, dia)


def _gerar_parcelas_con(con, matricula_id: int, qtd: int, total: float, inicio: str, dia: int) -> None:
    try:
        base = datetime.strptime(inicio[:10], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        base = date.today()
    dia = min(max(int(dia), 1), 28)
    valores = [round(total / qtd, 2)] * qtd
    valores[-1] = round(total - sum(valores[:-1]), 2)
    for i in range(qtd):
        venc = _somar_meses(base, i, dia)
        con.execute(
            """
            INSERT INTO parcelas (matricula_id, numero, valor, data_vencimento, situacao)
            VALUES (?, ?, ?, ?, 'pendente')
            """,
            (matricula_id, i + 1, valores[i], venc.isoformat()),
        )


def gerar_parcelas_se_faltando(matricula_id: int) -> None:
    with transacao() as con:
        m = con.execute("SELECT * FROM matriculas WHERE id=?", (matricula_id,)).fetchone()
        if not m:
            raise ValueError("Matrícula não encontrada.")
        n = con.execute(
            "SELECT COUNT(*) n FROM parcelas WHERE matricula_id=?", (matricula_id,)
        ).fetchone()["n"]
        if n:
            return
        _gerar_parcelas_con(
            con, matricula_id, int(m["qtd_parcelas"] or 1),
            float(m["valor_final"] or 0),
            m["data_inicio"] or m["data_matricula"],
            int(m["dia_vencimento"] or 10),
        )


def cancelar(mid: int, usuario_logado: dict) -> None:
    with transacao() as con:
        con.execute("UPDATE matriculas SET situacao='Cancelada' WHERE id=?", (mid,))
        con.execute(
            """
            UPDATE parcelas SET situacao='cancelada'
            WHERE matricula_id=? AND situacao IN ('pendente','parcial','atrasada')
            """,
            (mid,),
        )
    registrar_acao(usuario_logado["id"], "cancelar", "matriculas", mid)
