@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" desktop.py --trigger --colors amarelo
) else (
    py -3 desktop.py --trigger --colors amarelo
)
if errorlevel 1 pause
