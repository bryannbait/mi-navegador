@echo off
rem Lanza MiNavegador con el Python de su entorno virtual (venv).
cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
    echo.
    echo [ERROR] No encuentro el entorno virtual del proyecto.
    echo Crealo con:  python -m venv venv
    echo E instala:   venv\Scripts\pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

"venv\Scripts\python.exe" main.py
if errorlevel 1 pause
