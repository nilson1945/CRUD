"""Validações de formulário: CPF, e-mail, datas e valores."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Optional


def somente_digitos(texto: str) -> str:
    return re.sub(r"\D", "", texto or "")


def validar_cpf(cpf: str) -> bool:
    """Valida CPF brasileiro (dígitos verificadores). Vazio não é válido."""
    nums = somente_digitos(cpf)
    if len(nums) != 11 or nums == nums[0] * 11:
        return False
    soma = sum(int(nums[i]) * (10 - i) for i in range(9))
    d1 = (soma * 10) % 11
    if d1 == 10:
        d1 = 0
    if d1 != int(nums[9]):
        return False
    soma = sum(int(nums[i]) * (11 - i) for i in range(10))
    d2 = (soma * 10) % 11
    if d2 == 10:
        d2 = 0
    return d2 == int(nums[10])


def formatar_cpf(cpf: str) -> str:
    nums = somente_digitos(cpf)
    if len(nums) != 11:
        return cpf or ""
    return f"{nums[:3]}.{nums[3:6]}.{nums[6:9]}-{nums[9:]}"


def validar_email(email: str) -> bool:
    if not email:
        return False
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email.strip(), re.I))


def parse_data(texto: str) -> Optional[str]:
    """Aceita DD/MM/AAAA ou AAAA-MM-DD e devolve ISO (AAAA-MM-DD)."""
    texto = (texto or "").strip()
    if not texto:
        return None
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(texto, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def formatar_data(iso: Optional[str]) -> str:
    if not iso:
        return ""
    try:
        return datetime.strptime(iso[:10], "%Y-%m-%d").strftime("%d/%m/%Y")
    except ValueError:
        return iso


def parse_moeda(texto: str) -> Optional[float]:
    if texto is None:
        return None
    t = str(texto).strip()
    if not t:
        return None
    t = t.replace("R$", "").replace(" ", "")
    if "," in t and "." in t:
        t = t.replace(".", "").replace(",", ".")
    elif "," in t:
        t = t.replace(",", ".")
    try:
        return round(float(t), 2)
    except ValueError:
        return None


def formatar_moeda(valor: Optional[float]) -> str:
    if valor is None:
        return "R$ 0,00"
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def campo_obrigatorio(valor: str, nome: str) -> Optional[str]:
    if not (valor or "").strip():
        return f"O campo {nome} é obrigatório."
    return None
