@echo off
setlocal

cd /d "%~dp0"
title AJAX AI Server

echo Starting AJAX AI on http://127.0.0.1:8000/AJAX
echo Keep this window open while using the application.
echo.

python main.py --port 8000

if errorlevel 1 (
    echo.
    echo AJAX AI could not start. Check the error above.
    pause
)

endlocal
