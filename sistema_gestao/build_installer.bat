@echo off
chcp 65001 >nul
setlocal

echo ============================================
echo  Sistema de Gestao - Build do Instalador
echo ============================================
echo.

cd /d "%~dp0"

set "PYEXE=python"
if exist ".venv\Scripts\python.exe" set "PYEXE=.venv\Scripts\python.exe"

echo [1/2] Gerando executavel com PyInstaller...
%PYEXE% -m PyInstaller --noconfirm --clean build.spec
if errorlevel 1 (
    echo [ERRO] Falha ao gerar o executavel.
    pause
    exit /b 1
)

if not exist "dist\SistemaGestao.exe" (
    echo [ERRO] dist\SistemaGestao.exe nao foi criado.
    pause
    exit /b 1
)

echo.
echo [2/2] Compilando instalador com Inno Setup...

set "ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" (
    set "ISCC=C:\Program Files\Inno Setup 6\ISCC.exe"
)

if not exist "%ISCC%" (
    echo [ERRO] Inno Setup nao encontrado.
    echo Instale em: https://jrsoftware.org/isinfo.php
    pause
    exit /b 1
)

"%ISCC%" "%~dp0installer.iss"
if errorlevel 1 (
    echo [ERRO] Falha ao compilar o instalador.
    pause
    exit /b 1
)

echo.
echo ============================================
echo  Concluido!
echo  Executavel: dist\SistemaGestao.exe
echo  Instalador: installer_output\DimensaoLogus_Setup_2.0.0.exe
echo ============================================
pause
