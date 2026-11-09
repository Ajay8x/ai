@echo off
setlocal

title Stop AJAX AI
echo Stopping AJAX AI server...

taskkill /F /IM AJAX_AI.exe /T >nul 2>&1

if exist "%~dp0.ajax_ai.pid" (
    for /f "usebackq delims=" %%P in ("%~dp0.ajax_ai.pid") do taskkill /F /PID %%P /T >nul 2>&1
    del /q "%~dp0.ajax_ai.pid" >nul 2>&1
)

echo.
echo AJAX AI server stopped if it was running.
pause
endlocal
