@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

cd /d "%~dp0"

echo ========================================================
echo         Jarvis Computer Use Agent - Instalator
echo ========================================================

:: -------------------------------------------------------
:: 1. Szukamy odpowiedniej wersji Pythona (min. 3.11)
:: -------------------------------------------------------
set "PYTHON_CMD="

py -3.12 --version >nul 2>&1
if %errorlevel% equ 0 set "PYTHON_CMD=py -3.12"

if not defined PYTHON_CMD (
    py -3.11 --version >nul 2>&1
    if !errorlevel! equ 0 set "PYTHON_CMD=py -3.11"
)

if not defined PYTHON_CMD (
    echo Nie znaleziono wersji 3.11/3.12 przez launcher 'py'. Przeszukiwanie PATH...
    for /f "tokens=*" %%i in ('where python 2^>nul') do (
        "%%i" -c "import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)" >nul 2>&1
        if !errorlevel! equ 0 (
            echo Znaleziono Pythona: %%i
            set "PYTHON_CMD=%%i"
        )
    )
)

if not defined PYTHON_CMD (
    echo.
    echo NIE ZNALEZIONO PYTHON 3.11+.
    echo Proba automatycznej instalacji przez winget...
    echo.
    winget install -e --id Python.Python.3.12
    if !errorlevel! neq 0 (
        echo Instalacja nie powiodla sie. Zainstaluj Python 3.12+ recznie.
        pause
        exit /b 1
    )
    set "PYTHON_CMD=py -3.12"
)

:: -------------------------------------------------------
:: 2. Sprawdzanie Tesseract-OCR
:: -------------------------------------------------------
echo.
echo Sprawdzanie Tesseract-OCR...
where tesseract >nul 2>&1
if %errorlevel% neq 0 (
    if not exist "C:\Program Files\Tesseract-OCR\tesseract.exe" (
        echo Nie znaleziono Tesseract-OCR. Instalacja...
        winget install -e --id UB-Mannheim.TesseractOCR
        if !errorlevel! neq 0 (
            echo Tesseract-OCR nie zostal zainstalowany. OCR moze nie dzialac.
        ) else (
            echo Tesseract-OCR zainstalowany.
        )
    ) else (
        echo Znaleziono Tesseract w Program Files.
    )
) else (
    echo Tesseract-OCR jest w PATH.
)

:: -------------------------------------------------------
:: 3. Tworzenie .venv
:: -------------------------------------------------------
echo.
echo ========================================================
echo Tworzenie srodowiska .venv...
echo ========================================================

if not exist ".venv" (
    %PYTHON_CMD% -m venv .venv
    if !errorlevel! neq 0 (
        echo Blad tworzenia .venv.
        pause
        exit /b 1
    )
    echo .venv utworzone.
) else (
    echo .venv juz istnieje.
)

:: Rekreacja .venv jesli brak w nim pip (uszkodzony venv)
if not exist ".venv\Scripts\pip.exe" (
    echo .venv nie zawiera pip. Rekreacja...
    rmdir /s /q ".venv"
    %PYTHON_CMD% -m venv .venv
    if !errorlevel! neq 0 (
        echo Blad rekreacji .venv.
        pause
        exit /b 1
    )
)

:: -------------------------------------------------------
:: 4. Instalacja zależności
:: -------------------------------------------------------
echo.
echo Instalacja zaleznosci...
echo ========================================================

set "VENV_PYTHON=.venv\Scripts\python.exe"

if not exist "%VENV_PYTHON%" (
    echo Blad: brak .venv\Scripts\python.exe
    pause
    exit /b 1
)

"%VENV_PYTHON%" -m pip install --upgrade pip >nul
"%VENV_PYTHON%" -m pip install -r requirements.txt

if !errorlevel! neq 0 (
    echo Blad instalacji zaleznosci.
    pause
    exit /b 1
)

:: -------------------------------------------------------
:: 5. Uruchomienie
:: -------------------------------------------------------
echo.
echo ========================================================
echo Uruchamianie Jarvis...
echo ========================================================

call .venv\Scripts\activate.bat
python main.py

endlocal
pause
