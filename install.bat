@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

cd /d "%~dp0"

echo ========================================================
echo         Jarvis - Instalator srodowiska
echo ========================================================
echo.

:: -------------------------------------------------------
:: 1. Python
:: -------------------------------------------------------
set "PYTHON_CMD="

py -3.12 --version >nul 2>&1
if %errorlevel% equ 0 set "PYTHON_CMD=py -3.12"

if not defined PYTHON_CMD (
    py -3.11 --version >nul 2>&1
    if !errorlevel! equ 0 set "PYTHON_CMD=py -3.11"
)

if not defined PYTHON_CMD (
    for /f "tokens=*" %%i in ('where python 2^>nul') do (
        "%%i" -c "import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)" >nul 2>&1
        if !errorlevel! equ 0 set "PYTHON_CMD=%%i"
    )
)

if not defined PYTHON_CMD (
    echo [1/5] Python 3.11+ nie znaleziony. Instalacja przez winget...
    winget install -e --id Python.Python.3.12
    if !errorlevel! neq 0 (
        echo BLAD: Nie udalo sie zainstalowac Pythona. Zainstaluj recznie.
        pause
        exit /b 1
    )
    set "PYTHON_CMD=py -3.12"
)
echo [1/5] Python OK

:: -------------------------------------------------------
:: 2. .venv i zaleznosci (tylko jesli brak)
:: -------------------------------------------------------
echo [2/5] Konfiguracja srodowiska wirtualnego...

if exist ".venv\Lib\site-packages\PySide6\" (
    echo .venv juz gotowe - pomijam.
) else (
    if exist ".venv" rmdir /s /q ".venv"

    %PYTHON_CMD% -m venv .venv
    if !errorlevel! neq 0 (
        echo BLAD: Nie udalo sie utworzyc .venv.
        pause
        exit /b 1
    )

    set "VENV_PYTHON=.venv\Scripts\python.exe"
    "%VENV_PYTHON%" -m pip install --upgrade pip >nul
    "%VENV_PYTHON%" -m pip install -r requirements.txt
    if !errorlevel! neq 0 (
        echo BLAD: Nie udalo sie zainstalowac zaleznosci.
        pause
        exit /b 1
    )
)
echo [2/5] Zaleznosci OK

:: -------------------------------------------------------
:: 3. Tesseract-OCR
:: -------------------------------------------------------
echo [3/5] Sprawdzanie Tesseract-OCR...

where tesseract >nul 2>&1
if %errorlevel% equ 0 goto tesseract_done

if exist "C:\Program Files\Tesseract-OCR\tesseract.exe" (
    echo Znalaziono Tesseract w Program Files.
    goto tesseract_done
)

echo Instalowanie Tesseract-OCR przez winget...
winget install -e --id UB-Mannheim.TesseractOCR
if !errorlevel! neq 0 (
    echo OSTRZEZENIE: Nie udalo sie zainstalowac Tesseract-OCR.
    echo Mozesz zainstalowac recznie z: https://github.com/UB-Mannheim/tesseract/wiki
    echo lub ustawic sciezke w konfiguracji Jarvisa.
    goto tesseract_done
)
echo Tesseract-OCR zainstalowany.

:tesseract_done
echo [3/5] Tesseract OK

:: -------------------------------------------------------
:: 4. Ollama
:: -------------------------------------------------------
echo [4/5] Sprawdzanie Ollama...

where ollama >nul 2>&1
if %errorlevel% equ 0 goto ollama_done

echo Instalowanie Ollama przez winget...
winget install -e --id Ollama.Ollama
if !errorlevel! neq 0 (
    echo OSTRZEZENIE: Winget nie dziala. Probuje instalator offline...
    curl -sL -o "%TEMP%\OllamaSetup.exe" https://ollama.com/download/OllamaSetup.exe
    if exist "%TEMP%\OllamaSetup.exe" (
        start /wait "" "%TEMP%\OllamaSetup.exe" /silent
        echo Zainstalowano. Uruchom ponownie install.bat po zakonczeniu.
    ) else (
        echo OSTRZEZENIE: Nie udalo sie zainstalowac Ollamy.
        echo Mozesz zainstalowac recznie z: https://ollama.com/download
    )
    goto ollama_skip_model
)
echo Ollama zainstalowana.

:ollama_done
echo.
set /p PULL_MODEL="Czy chcesz pobrac model lokalny sam860/dolphin3-qwen2.5:3b (~2GB)? (t/n): "
if /i "!PULL_MODEL!" neq "t" (
    echo Pomijam pobieranie modelu. Mozesz pobrac recznie: ollama pull sam860/dolphin3-qwen2.5:3b
    goto ollama_skip_model
)
echo [4/5] Sprawdzanie modelu lokalnego...
echo Sprawdzanie polaczenia z Ollama...
powershell -Command "try { $r = Invoke-WebRequest -Uri 'http://localhost:11434/api/tags' -TimeoutSec 5 -ErrorAction Stop; exit 0 } catch { exit 1 }" >nul 2>&1
if %errorlevel% neq 0 (
    echo Ollama nie odpowiada - uruchom ja recznie lub pomijn krok.
    goto ollama_skip_model
)
echo Pobieranie modelu sam860/dolphin3-qwen2.5:3b (~2GB). To moze zajac kilka minut...
ollama pull sam860/dolphin3-qwen2.5:3b
if %errorlevel% neq 0 (
    echo OSTRZEZENIE: Nie udalo sie pobrac modelu.
    echo Po instalacji uruchom: ollama pull sam860/dolphin3-qwen2.5:3b
    goto ollama_skip_model
)
:ollama_skip_model
echo [4/5] Ollama OK

:: -------------------------------------------------------
echo.
echo ========================================================
echo Instalacja zakonczona. Uzyj start.bat aby uruchomic.
echo ========================================================
pause
