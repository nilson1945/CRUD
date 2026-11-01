"""Parcelas, pagamentos e indicadores financeiros."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

from database import get_connection, transacao, registrar_acao
from validacoes import parse_moeda

FORMAS = [
    "Dinheiro", "PIX", "Cartão de crédito", "Cartão de débito",
    "Boleto", "Transferência bancária",
]


def _saldo_parcela(con, parcela_id: int) -> tuple[dict, float]:
    p = con.execute("SELECT * FROM parcelas WHERE id=?", (parcela_id,)).fetchone()
    if not p:
        raise ValueError("Parcela não encontrada.")
    pago = con.execute(
        "SELECT COALESCE(SUM(valor_pago),0) s FROM pagamentos WHERE parcela_id=?",
        (parcela_id,),
    ).fetchone()["s"]
    devido = float(p["valor"]) + float(p["juros"] or 0) + float(p["multa"] or 0) - float(p["desconto"] or 0)
    return dict(p), round(devido - float(pago), 2)


def atualizar_situacoes_atraso() -> None:
    hoje = date.today().isoformat()
    with get_connection() as con:
        con.execute(
            """
            UPDATE parcelas SET situacao='atrasada'
            WHERE situacao IN ('pendente','parcial') AND data_vencimento < ?
            """,
            (hoje,),
        )
        con.commit()


def listar_parcelas(filtro: str = "todas", busca: str = "") -> list[dict]:
    atualizar_situacoes_atraso()
    sql = """
        SELECT p.*, m.numero_matricula, cl.nome AS cliente_nome, c.nome AS curso_nome,
               cl.id AS cliente_id,
               (p.valor + p.juros + p.multa - p.desconto) AS valor_devido,
               COALESCE((SELECT SUM(valor_pago) FROM pagamentos g WHERE g.parcela_id=p.id),0) AS valor_pago
        FROM parcelas p
        JOIN matriculas m ON m.id = p.matricula_id
        JOIN clientes cl ON cl.id = m.cliente_id
        JOIN cursos c ON c.id = m.curso_id
        WHERE p.situacao != 'cancelada'
    """
    params: list[Any] = []
    hoje = date.today().isoformat()
    if filtro == "pendentes":
        sql += " AND p.situacao IN ('pendente','parcial')"
    elif filtro == "vencidas":
        sql += " AND p.situacao IN ('pendente','parcial','atrasada') AND p.data_vencimento < ?"
        params.append(hoje)
    elif filtro == "a_vencer":
        sql += " AND p.situacao IN ('pendente','parcial') AND p.data_vencimento >= ?"
        params.append(hoje)
    elif filtro == "pagas":
        sql += " AND p.situacao='paga'"
    if busca.strip():
        like = f"%{busca.strip()}%"
        sql += " AND (cl.nome LIKE ? OR m.numero_matricula LIKE ? OR c.nome LIKE ?)"
        params.extend([like, like, like])
    sql += " ORDER BY p.data_vencimento, cl.nome"
    with get_connection() as con:
        return [dict(r) for r in con.execute(sql, params)]


def registrar_pagamento(
    parcela_id: int,
    valor_pago: Any,
    forma: str,
    data_pag: Optional[str],
    observacao: str,
    usuario_logado: dict,
) -> int:
    if isinstance(valor_pago, str):
        valor_pago = parse_moeda(valor_pago)
    if not valor_pago or valor_pago <= 0:
        raise ValueError("Informe um valor pago válido.")
    if forma not in FORMAS:
        raise ValueError("Forma de pagamento inválida.")
    data_pag = data_pag or date.today().isoformat()

    with transacao() as con:
        parcela, saldo = _saldo_parcela(con, parcela_id)
        if parcela["situacao"] == "cancelada":
            raise ValueError("Não é possível pagar parcela cancelada.")
        if parcela["situacao"] == "paga":
            raise ValueError("Esta parcela já está paga.")
        mat = con.execute(
            "SELECT cliente_id, id FROM matriculas WHERE id=?",
            (parcela["matricula_id"],),
        ).fetchone()
        cur = con.execute(
            """
            INSERT INTO pagamentos (
                cliente_id, matricula_id, parcela_id, valor_pago, data_pagamento,
                forma_pagamento, observacao, funcionario_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                mat["cliente_id"], mat["id"], parcela_id, float(valor_pago),
                data_pag, forma, observacao, usuario_logado.get("id"),
            ),
        )
        pid = int(cur.lastrowid)
        novo_saldo = round(saldo - float(valor_pago), 2)
        if novo_saldo <= 0.009:
            sit = "paga"
        elif date.fromisoformat(parcela["data_vencimento"]) < date.today():
            sit = "atrasada"
        else:
            sit = "parcial"
        con.execute("UPDATE parcelas SET situacao=? WHERE id=?", (sit, parcela_id))
    registrar_acao(
        usuario_logado["id"], "pagamento", "pagamentos", pid,
        f"Parcela {parcela_id} R$ {valor_pago}",
    )
    return pid


def aplicar_encargos(parcela_id: int, juros: float, multa: float, desconto: float, usuario_logado: dict) -> None:
    with transacao() as con:
        con.execute(
            "UPDATE parcelas SET juros=?, multa=?, desconto=? WHERE id=? AND situacao!='cancelada'",
            (float(juros or 0), float(multa or 0), float(desconto or 0), parcela_id),
        )
    registrar_acao(usuario_logado["id"], "encargos", "parcelas", parcela_id)


def indicadores(mes: Optional[str] = None) -> dict:
    """mes no formato AAAA-MM. Não conta parcelas canceladas como recebidas."""
    atualizar_situacoes_atraso()
    mes = mes or date.today().strftime("%Y-%m")
    inicio, fim = f"{mes}-01", f"{mes}-31"
    with get_connection() as con:
        recebido_mes = con.execute(
            """
            SELECT COALESCE(SUM(g.valor_pago),0) s
            FROM pagamentos g
            JOIN parcelas p ON p.id = g.parcela_id
            WHERE p.situacao != 'cancelada'
              AND g.data_pagamento BETWEEN ? AND ?
            """,
            (inicio, fim),
        ).fetchone()["s"]
        a_receber = con.execute(
            """
            SELECT COALESCE(SUM(p.valor + p.juros + p.multa - p.desconto),0)
                 - COALESCE((SELECT SUM(g.valor_pago) FROM pagamentos g
                             JOIN parcelas p2 ON p2.id=g.parcela_id
                             WHERE p2.situacao IN ('pendente','parcial','atrasada')),0) s
            FROM parcelas p
            WHERE p.situacao IN ('pendente','parcial','atrasada')
            """
        ).fetchone()["s"]
        atraso = con.execute(
            """
            SELECT COALESCE(SUM(
                p.valor + p.juros + p.multa - p.desconto
                - COALESCE((SELECT SUM(g.valor_pago) FROM pagamentos g WHERE g.parcela_id=p.id),0)
            ),0) s
            FROM parcelas p
            WHERE p.situacao IN ('pendente','parcial','atrasada') AND p.data_vencimento < ?
            """,
            (date.today().isoformat(),),
        ).fetchone()["s"]
        total_pagamentos = con.execute(
            """
            SELECT COALESCE(SUM(g.valor_pago),0) s
            FROM pagamentos g
            JOIN parcelas p ON p.id = g.parcela_id
            WHERE p.situacao != 'cancelada'
            """
        ).fetchone()["s"]
        pendentes_qtd = con.execute(
            "SELECT COUNT(*) n FROM parcelas WHERE situacao IN ('pendente','parcial','atrasada')"
        ).fetchone()["n"]
    return {
        "recebido_mes": float(recebido_mes or 0),
        "a_receber": float(a_receber or 0),
        "atraso": float(atraso or 0),
        "total_pagamentos": float(total_pagamentos or 0),
        "pendentes_qtd": int(pendentes_qtd or 0),
    }


def clientes_inadimplentes() -> list[dict]:
    atualizar_situacoes_atraso()
    hoje = date.today().isoformat()
    with get_connection() as con:
        rows = con.execute(
            """
            SELECT cl.id, cl.nome, cl.telefone,
                   COUNT(p.id) AS parcelas_atraso,
                   SUM(p.valor + p.juros + p.multa - p.desconto
                       - COALESCE((SELECT SUM(g.valor_pago) FROM pagamentos g WHERE g.parcela_id=p.id),0)
                   ) AS valor_atraso
            FROM parcelas p
            JOIN matriculas m ON m.id = p.matricula_id
            JOIN clientes cl ON cl.id = m.cliente_id
            WHERE p.situacao IN ('pendente','parcial','atrasada') AND p.data_vencimento < ?
            GROUP BY cl.id
            ORDER BY valor_atraso DESC
            """,
            (hoje,),
        ).fetchall()
        return [dict(r) for r in rows]


def recebimentos_por_mes(ano: Optional[int] = None) -> list[tuple[str, float]]:
    ano = ano or date.today().year
    with get_connection() as con:
        rows = con.execute(
            """
            SELECT substr(g.data_pagamento,1,7) mes, SUM(g.valor_pago) total
            FROM pagamentos g
            JOIN parcelas p ON p.id = g.parcela_id
            WHERE p.situacao != 'cancelada' AND g.data_pagamento LIKE ?
            GROUP BY mes ORDER BY mes
            """,
            (f"{ano}-%",),
        ).fetchall()
        return [(r["mes"], float(r["total"])) for r in rows]


def obter_parcela(parcela_id: int) -> Optional[dict]:
    with get_connection() as con:
        row = con.execute(
            """
            SELECT p.*, m.numero_matricula, cl.nome AS cliente_nome, cl.id AS cliente_id
            FROM parcelas p
            JOIN matriculas m ON m.id = p.matricula_id
            JOIN clientes cl ON cl.id = m.cliente_id
            WHERE p.id=?
            """,
            (parcela_id,),
        ).fetchone()
        return dict(row) if row else None
