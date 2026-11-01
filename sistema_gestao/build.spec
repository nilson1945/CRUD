# -*- mode: python ; coding: utf-8 -*-
"""
Arquivo de especificação do PyInstaller para o Sistema de Gestão Empresarial
(Dimensão do Logus).

Uso:
    pyinstaller build.spec
"""

from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

ROOT = Path(SPECPATH)

# CustomTkinter precisa dos temas/arquivos internos no pacote
datas = collect_data_files("customtkinter")
# matplotlib (gráficos do dashboard) e reportlab (PDF) carregam dados em tempo de execução
datas += collect_data_files("matplotlib")
datas += collect_data_files("reportlab")
datas += collect_data_files("openpyxl")

hiddenimports = collect_submodules("customtkinter") + [
    "PIL",
    "PIL._tkinter_finder",
    "sqlite3",
    "bcrypt",
    "tkinter",
    "tkinter.ttk",
    "tkinter.filedialog",
    "tkinter.messagebox",
    "matplotlib.backends.backend_tkagg",
    "reportlab.pdfbase._fontdata",
    "reportlab.rl_config",
    "openpyxl",
    "et_xmlfile",
]

a = Analysis(
    [str(ROOT / "main.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tests"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="SistemaGestao",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Sem janela de console (aplicação GUI)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Adicione caminho para .ico se tiver: str(ROOT / "assets" / "icones" / "app.ico")
)
