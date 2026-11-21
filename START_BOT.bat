@echo off
chcp 65001 >nul
title Rail Nation - Bonusy i Reklamy
cd /d "%~dp0"

echo ==================================================
echo   RAIL NATION - BOT BONUSY, REKLAMY I POLLUX
echo ==================================================
echo.

:: Sprawdzenie czy Python jest zainstalowany
python --version >nul 2>&1
if errorlevel 1 (
    echo [BLAD] Nie wykryto Pythona w systemie!
    echo Zainstaluj Pythona ze strony: https://www.python.org/downloads/
    echo WAZNE: Podczas instalacji zaznacz opcje "Add Python to PATH".
    echo.
    pause
    exit /b 1
)

:: Sprawdzenie czy wymagane biblioteki sa juz zainstalowane
echo Sprawdzanie wymaganych bibliotek...
python -c "import pyautogui, cv2, PIL" >nul 2>&1
if errorlevel 1 (
    echo.
    echo Pierwsze uruchomienie lub brak bibliotek. Instaluje wymagane pakiety...
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo [BLAD] Nie udalo sie zainstalowac bibliotek! Sprawdz polaczenie z internetem.
        pause
        exit /b 1
    )
    echo.
    echo Biblioteki zainstalowane pomyslnie!
) else (
    echo Wszystkie biblioteki sa gotowe.
)

echo.
echo Uruchamiam bota...
echo (Aby zatrzymac bota, zamknij to okno lub nacisnij Ctrl+C.)
echo.
python main.py

echo.
echo Bot zakonczyl prace.
pause