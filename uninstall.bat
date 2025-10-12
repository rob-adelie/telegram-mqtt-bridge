@echo off
setlocal

echo This will remove the Telegram-MQTT Bridge installation
echo.
echo The following will be removed:
echo - Virtual environment (venv folder)
echo - Startup shortcut
echo - Logs folder
echo.
echo Configuration files will be preserved.
echo.
set /p confirm="Are you sure you want to continue? (y/N): "
if /i not "%confirm%"=="y" (
    echo Uninstall cancelled.
    pause
    exit /b 0
)

echo.
echo Removing Telegram-MQTT Bridge...

:: Remove startup shortcut
set "startup_folder=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "shortcut_name=telegram-mqtt-bridge.lnk"

if exist "%startup_folder%\%shortcut_name%" (
    echo Removing startup shortcut...
    del "%startup_folder%\%shortcut_name%"
    if errorlevel 1 (
        echo WARNING: Failed to remove startup shortcut
    ) else (
        echo ✓ Startup shortcut removed
    )
) else (
    echo ✓ No startup shortcut found
)

:: Remove virtual environment
if exist "venv" (
    echo Removing virtual environment...
    rmdir /s /q "venv"
    if errorlevel 1 (
        echo WARNING: Failed to remove virtual environment
        echo You may need to manually delete the 'venv' folder
    ) else (
        echo ✓ Virtual environment removed
    )
) else (
    echo ✓ No virtual environment found
)

:: Remove logs folder (optional - ask user)
if exist "logs" (
    echo.
    set /p remove_logs="Remove logs folder? (y/N): "
    if /i "%remove_logs%"=="y" (
        rmdir /s /q "logs"
        if errorlevel 1 (
            echo WARNING: Failed to remove logs folder
        ) else (
            echo ✓ Logs folder removed
        )
    ) else (
        echo ✓ Logs folder preserved
    )
) else (
    echo ✓ No logs folder found
)

echo.
echo Uninstall complete!
echo.
echo Note: Configuration files have been preserved.
echo To completely remove the project, manually delete the project folder.
echo.
pause