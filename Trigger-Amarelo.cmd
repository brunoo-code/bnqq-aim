@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" desktop.py --trigger --config trigger.json
) else (
    py -3 desktop.py --trigger --config trigger.json
)
if errorlevel 1 pause
