"""Atalho na raiz do projeto para iniciar o sistema gráfico."""

from pathlib import Path
import runpy
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "sistema_gestao"))
runpy.run_path(str(Path(__file__).resolve().parent / "sistema_gestao" / "main.py"), run_name="__main__")
