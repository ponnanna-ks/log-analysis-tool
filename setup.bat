@echo off
setlocal enabledelayedexpansion

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

:: Check Python version
for /f "tokens=2" %%I in ('python --version 2^>^&1') do set PYTHON_VERSION=%%I
for /f "tokens=1,2 delims=." %%a in ("!PYTHON_VERSION!") do (
    set MAJOR=%%a
    set MINOR=%%b
)

if !MAJOR! LSS 3 (
    echo Error: Python 3.6 or higher is required. Found version !PYTHON_VERSION!
    pause
    exit /b 1
)

if !MAJOR! EQU 3 (
    if !MINOR! LSS 6 (
        echo Error: Python 3.6 or higher is required. Found version !PYTHON_VERSION!
        pause
        exit /b 1
    )
)

:: Remove existing virtual environment if it exists
if exist venv (
    echo Removing existing virtual environment...
    rmdir /s /q venv
)

echo Creating Python virtual environment...
python -m venv venv
if errorlevel 1 (
    echo Error: Failed to create virtual environment
    pause
    exit /b 1
)

echo Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo Error: Failed to activate virtual environment
    pause
    exit /b 1
)

echo Upgrading pip...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo Error: Failed to upgrade pip
    pause
    exit /b 1
)

echo Installing required packages...
pip install -r requirements.txt
if errorlevel 1 (
    echo Error: Failed to install required packages
    pause
    exit /b 1
)

echo Setup complete!
echo To run the application, use: venv\Scripts\activate.bat ^&^& python log_analysis_ui.py
pause 