@echo off
setlocal

:: Use current directory instead of assuming path
set "project_dir=%~dp0"
set "python_script_name=telegram-mqtt-bridge.py"

:: Check if we're in the right directory
if not exist "%python_script_name%" (
    echo ERROR: %python_script_name% not found in current directory
    echo Please run this script from the telegram-mqtt-bridge directory
    pause
    exit /b 1
)

:: Check if virtual environment exists
if not exist "venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found
    echo Please run install.bat first to set up the environment
    pause
    exit /b 1
)

:: Check if config file exists and is configured
if not exist "telegram-mqtt-bridge.cfg" (
    echo ERROR: Configuration file telegram-mqtt-bridge.cfg not found
    echo Please create and configure this file before running
    pause
    exit /b 1
)

:: Check if config file has placeholder values
findstr /C:"<Your telegram bot token>" telegram-mqtt-bridge.cfg >nul
if not errorlevel 1 (
    echo ERROR: Configuration file contains placeholder values
    echo Please edit telegram-mqtt-bridge.cfg with your actual settings
    pause
    exit /b 1
)

:: Create logs directory if it doesn't exist
if not exist "logs" mkdir logs

echo Starting Telegram-MQTT Bridge...
echo Press Ctrl+C to stop
echo.

:: Activate virtual environment and run the application
call "venv\Scripts\activate.bat"
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

:: Run the application
python telegram-mqtt-bridge.py

:: If we get here, the application has stopped
echo.
echo Telegram-MQTT Bridge has stopped.
pause