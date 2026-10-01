@echo off
title ExpenseFlow Runner
cd /d "%~dp0"

echo ========================================================
echo               ExpenseFlow Quick Launcher
echo ========================================================
echo.

:: Ensure backend\.env exists
if not exist "backend\.env" (
    echo [.env] Setting up backend\.env from template...
    copy "backend\.env.example" "backend\.env" >nul
)

:: Run via python main.py
python main.py %*

if %ERRORLEVEL% neq 0 (
    echo.
    echo Server stopped or error occurred.
    pause
)
