@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================================
echo         Jarvis Computer Use Agent
echo ========================================================

if not exist ".venv\Scripts\python.exe" (
    echo Srodowisko .venv nie istnieje.
    echo Uruchom najpierw install.bat
    pause
    exit /b 1
)

if not exist ".venv\Lib\site-packages\PySide6" (
    echo Zaleznosci nie sa zainstalowane.
    echo Uruchom najpierw install.bat
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat
python main.py

pause
