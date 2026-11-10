@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" painel.py
) else (
    py -3 painel.py
)
if errorlevel 1 pause
