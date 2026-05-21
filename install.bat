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
        if !errorlevel! equ 0 (
            set "PYTHON_CMD=%%i"
        )
    )
)

if not defined PYTHON_CMD (
    echo [1/5] Python 3.11+ nie znaleziony. Instalacja przez winget...
    winget install -e --id Python.Python.3.12
    if !errorlevel! neq 0 (
        echo BLAD: Nie udalo sie zainstalowac Pythona.
        pause
        exit /b 1
    )
    set "PYTHON_CMD=py -3.12"
) else (
    echo [1/5] Python OK: %PYTHON_CMD%
)

:: -------------------------------------------------------
:: 2. .venv i zależności
:: -------------------------------------------------------
echo [2/5] Konfiguracja srodowiska wirtualnego...

if exist ".venv" (
    rmdir /s /q ".venv"
)

%PYTHON_CMD% -m venv .venv
if !errorlevel! neq 0 (
    echo BLAD: Nie udalo sie utworzyc .venv.
    pause
    exit /b 1
)

set "VENV_PYTHON=.venv\Scripts\python.exe"
"%VENV_PYTHON%" -m pip install --upgrade pip >nul

echo Instalowanie zaleznosci...
"%VENV_PYTHON%" -m pip install -r requirements.txt
if !errorlevel! neq 0 (
    echo BLAD: Nie udalo sie zainstalowac zaleznosci.
    pause
    exit /b 1
)
echo [2/5] Zaleznosci zainstalowane.

:: -------------------------------------------------------
:: 3. Tesseract-OCR
:: -------------------------------------------------------
echo [3/5] Sprawdzanie Tesseract-OCR...

where tesseract >nul 2>&1
if %errorlevel% neq 0 (
    if not exist "C:\Program Files\Tesseract-OCR\tesseract.exe" (
        echo Instalowanie Tesseract-OCR przez winget...
        winget install -e --id UB-Mannheim.TesseractOCR
        if !errorlevel! neq 0 (
            echo OSTRZEZENIE: Tesseract-OCR nie zostal zainstalowany.
            echo OCR moze nie dzialac. Mozesz zainstalowac recznie z:
            echo https://github.com/UB-Mannheim/tesseract/wiki
        ) else (
            echo Tesseract-OCR zainstalowany.
        )
    ) else (
        echo Tesseract-OCR znaleziony w Program Files.
    )
) else (
    echo Tesseract-OCR OK (w PATH).
)
echo [3/5] Tesseract OK.

:: -------------------------------------------------------
:: 4. Ollama
:: -------------------------------------------------------
echo [4/5] Sprawdzanie Ollama...

where ollama >nul 2>&1
if %errorlevel% neq 0 (
    echo Instalowanie Ollama przez winget...
    winget install -e --id Ollama.Ollama
    if !errorlevel! neq 0 (
        echo OSTRZEZENIE: Nie udalo sie zainstalowac Ollamy przez winget.
        echo Mozesz zainstalowac recznie z: https://ollama.com/download
        echo.
        echo Instalator Ollamy wymaga potwierdzenia UAC.
        echo Pobieram i uruchamiam instalator...
        curl -L -o "%TEMP%\OllamaSetup.exe" https://ollama.com/download/OllamaSetup.exe
        if exist "%TEMP%\OllamaSetup.exe" (
            "%TEMP%\OllamaSetup.exe" /silent
            echo Ollama zainstalowana. Uruchamianie...
        ) else (
            echo BLAD: Nie udalo sie pobrac instalatora Ollamy.
        )
    ) else (
        echo Ollama zainstalowana przez winget.
    )
) else (
    echo Ollama OK.
)

:: -------------------------------------------------------
:: 5. Model lokalny (qwen2.5:3b)
:: -------------------------------------------------------
echo [5/5] Pobieranie modelu lokalnego (qwen2.5:3b)...

:: Sprawdzamy czy ollama jest dostepna (po instalacji moze byc w PATH dopiero po odswiezeniu)
where ollama >nul 2>&1
if %errorlevel% equ 0 (
    echo Pobieranie ~2GB. To moze zajac kilka minut...
    ollama pull qwen2.5:3b
    if !errorlevel! equ 0 (
        echo Model qwen2.5:3b gotowy.
    ) else (
        echo OSTRZEZENIE: Nie udalo sie pobrac modelu.
        echo Mozesz pobrac recznie: ollama pull qwen2.5:3b
    )
) else (
    echo OSTRZEZENIE: Ollama niedostepna - pomijam pobieranie modelu.
    echo Po instalacji Ollamy uruchom: ollama pull qwen2.5:3b
)
echo [5/5] Gotowe.

echo.
echo ========================================================
echo Instalacja zakonczona. Uzyj start.bat aby uruchomic.
echo ========================================================
pause
