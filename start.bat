@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo  UNA# ASISTENT — pokretanje...
python --version >nul 2>&1
if errorlevel 1 (
    echo  [!] Python nije pronađen. Preuzmi: https://www.python.org/downloads/ i oznaci "Add Python to PATH".
    pause
    exit /b
)
if not exist "venv\" python -m venv venv
call venv\Scripts\activate.bat
pip install -r requirements.txt -q
if /i "%1"=="web" (streamlit run app.py) else (python una_cli.py)
pause
