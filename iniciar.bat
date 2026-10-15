@echo off
cd /d "%~dp0"
call venv\Scripts\activate
python main.py
if errorlevel 1 pause