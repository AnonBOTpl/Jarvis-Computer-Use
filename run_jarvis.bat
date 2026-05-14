@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================================
echo         Jarvis Computer Use Agent - Instalator
echo ========================================================

:: 1. Szukamy odpowiedniej wersji Pythona używając narzędzia `py`
set "PYTHON_EXE="

:: Sprawdzanie py -3.12
py -3.12 --version >nul 2>&1
if %errorlevel% equ 0 (
    echo Znalaziono Python 3.12 przez launcher 'py'.
    set "PYTHON_CMD=py -3.12"
    goto setup_venv
)

:: Sprawdzanie py -3.11
py -3.11 --version >nul 2>&1
if %errorlevel% equ 0 (
    echo Znalaziono Python 3.11 przez launcher 'py'.
    set "PYTHON_CMD=py -3.11"
    goto setup_venv
)

:: Jeśli 'py' nie znalazło, próbujemy 'where python'
echo Nie znaleziono wersji 3.11/3.12 przez launcher 'py'. Przeszukiwanie systemowego PATH...
for /f "tokens=*" %%i in ('where python 2^>nul') do (
    %%i -c "import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)" >nul 2>&1
    if !errorlevel! equ 0 (
        echo Znaleziono odpowiedniego Pythona: %%i
        set "PYTHON_CMD=%%i"
        goto setup_venv
    )
)

:: Jeśli nie znaleziono żadnej odpowiedniej wersji, próbujemy instalacji przez winget
echo.
echo NIE ZNALEZIONO ODPOWIEDNIEJ WERSJI PYTHON (min. 3.11).
echo Próba automatycznej instalacji poprzez winget...
echo UWAGA: Może pojawić się prośba o uprawnienia administratora (UAC). Proszę potwierdzić.
echo.

winget install -e --id Python.Python.3.12
if %errorlevel% neq 0 (
    echo Instalacja Pythona nie powiodła się. Zainstaluj Pythona 3.12 ręcznie i spróbuj ponownie.
    pause
    exit /b 1
)

:: Po instalacji przypisujemy polecenie (może wymagać restartu terminala, ale próbujemy `py`)
set "PYTHON_CMD=py -3.12"

:setup_venv
echo.
echo ========================================================
echo Tworzenie środowiska wirtualnego .venv...
echo ========================================================

if not exist ".venv" (
    %PYTHON_CMD% -m venv .venv
    if !errorlevel! neq 0 (
        echo Błąd podczas tworzenia środowiska wirtualnego.
        pause
        exit /b 1
    )
    echo Srodowisko .venv utworzone pomyslnie.
) else (
    echo Srodowisko .venv juz istnieje.
)

echo.
echo Aktywacja srodowiska i instalacja zaleznosci...
echo ========================================================

:: Zamiast wywoływać skrypt aktywacji, używamy bezpośrednio ścieżki do pythona z venv
set "VENV_PYTHON=.venv\Scripts\python.exe"

if not exist "%VENV_PYTHON%" (
    echo Blad: Nie znaleziono .venv\Scripts\python.exe. Srodowisko moze byc uszkodzone.
    pause
    exit /b 1
)

:: Aktualizacja pip
"%VENV_PYTHON%" -m pip install --upgrade pip

:: Instalacja zaleznosci
echo Instalowanie wymaganych pakietów z pliku requirements.txt...
"%VENV_PYTHON%" -m pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo Wystapil blad podczas instalacji zaleznosci.
    pause
    exit /b 1
)

echo.
echo ========================================================
echo Konfiguracja zakonczona sukcesem. Uruchamiam Jarvis...
echo ========================================================

:: Uruchomienie aplikacji
"%VENV_PYTHON%" main.py

pause
