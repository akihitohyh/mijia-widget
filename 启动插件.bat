@echo off
cd /d "%~dp0"

if exist "venv\Scripts\python.exe" (
    venv\Scripts\python.exe main_widget.py
) else (
    python main_widget.py
)

if errorlevel 1 pause
