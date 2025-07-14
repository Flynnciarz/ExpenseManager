@echo off
title Secure Expense Management System
echo.
echo ================================================
echo    SECURE EXPENSE MANAGEMENT SYSTEM
echo ================================================
echo.
echo Starting the application...
echo.

cd /d "%~dp0"
if exist "dist\ExpenseManager.exe" (
    "dist\ExpenseManager.exe"
) else if exist "ExpenseManager.exe" (
    "ExpenseManager.exe"
) else (
    echo Error: ExpenseManager.exe not found!
    echo Please ensure the executable is in the same directory.
    pause
)

echo.
echo Application closed.
pause
