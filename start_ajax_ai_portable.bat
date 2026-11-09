@echo off
setlocal

cd /d "%~dp0"
title AJAX AI Portable

echo Starting bundled AJAX AI and opening the browser...
echo Keep this window open while using the application.
echo.

AJAX_AI.exe

if errorlevel 1 (
    echo.
    echo AJAX_AI.exe could not start. Check the error above.
    pause
)

endlocal
