@echo off
setlocal

cd /d "%~dp0"
title Build AJAX AI EXE

echo Building AJAX AI portable Windows application...
echo This includes the Python runtime and the local AI model.
echo The final folder may be about 2.5 GB because of the GGUF and PyTorch models.
echo.

python -m PyInstaller --noconfirm --clean --onedir --name AJAX_AI ^
  --add-data "data\intents.json;data" ^
  --add-data "data\intent_variants.json;data" ^
  --add-data "data\intent_expansion.json;data" ^
  --add-data "data\knowledge;data\knowledge" ^
  --add-data "models;models" ^
  --add-data "views;views" ^
  --add-data "frontend;frontend" ^
  --add-data "plugins;plugins" ^
  --add-data "model_capabilities.yaml;." ^
  --hidden-import "multipart" ^
  --hidden-import "uvicorn.logging" ^
  --hidden-import "uvicorn.loops.auto" ^
  --hidden-import "uvicorn.protocols.http.auto" ^
  --hidden-import "uvicorn.protocols.websockets.auto" ^
  --hidden-import "ai.llm.gguf_provider" ^
  main.py

if errorlevel 1 (
    echo.
    echo Build failed. Check the error above.
    pause
    exit /b 1
)

if not exist "dist\AJAX_AI\AJAX_AI.exe" (
    echo.
    echo Build finished without producing dist\AJAX_AI\AJAX_AI.exe.
    pause
    exit /b 1
)

copy /y start_ajax_ai_portable.bat dist\AJAX_AI\start_ajax_ai.bat >nul
if errorlevel 1 exit /b 1
copy /y kill_ajax_ai.bat dist\AJAX_AI\kill_ajax_ai.bat >nul
if errorlevel 1 exit /b 1

echo.
echo Build complete.
echo EXE: %~dp0dist\AJAX_AI\AJAX_AI.exe
echo Double-click AJAX_AI.exe to start the app and open the browser.
echo.
pause
endlocal
