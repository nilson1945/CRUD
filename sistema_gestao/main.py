"""Ponto de entrada do sistema de gestão empresarial."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import customtkinter as ctk

from database import inicializar_banco
from interfaces.tela_login import TelaLogin
from interfaces.tela_principal import TelaPrincipal


def main() -> None:
    inicializar_banco()
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")
    login = TelaLogin()
    login.mainloop()
    if not login.usuario:
        return
    app = TelaPrincipal(login.usuario)
    app.mainloop()


if __name__ == "__main__":
    main()
