@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo ZVideoGridPlayer Launcher
echo ========================================
echo Current directory: %CD%
echo.

:: Проверяем виртуальное окружение
if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found at .venv\
    echo Please create it with: python -m venv .venv
    pause
    exit /b 1
)

:: Проверяем наличие модуля main.py
if not exist "scr\ZVideoGridPlayer\main.py" (
    echo [ERROR] Module not found: scr.ZVideoGridPlayer.main
    echo Expected file: scr\ZVideoGridPlayer\main.py
    echo.
    echo Available files in scr\ZVideoGridPlayer\:
    dir scr\ZVideoGridPlayer\*.py 2>nul
    pause
    exit /b 1
)

:: Проверяем наличие __init__.py (необязательно, но полезно)
if not exist "scr\ZVideoGridPlayer\__init__.py" (
    echo [WARNING] __init__.py not found in scr\ZVideoGridPlayer\
    echo Module may not work correctly
    echo.
)

echo [INFO] Virtual environment found
echo [INFO] Module found: scr.ZVideoGridPlayer.main
echo.

:: Запускаем
echo [INFO] Starting ZVideoGridPlayer...
echo ========================================
echo.

.venv\Scripts\python.exe -m scr.ZVideoGridPlayer.main

:: Проверяем результат
echo.
echo ========================================
if errorlevel 1 (
    echo [ERROR] Application crashed with code %errorlevel%
    echo.
    pause
) else (
    echo [INFO] Application closed successfully
    :: No pause here - window will close automatically
)

:: Убираем лишний pause при успешном завершении