@echo off
setlocal
cd /d "%~dp0"
set "RESULT=0"
if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Run setup.bat first.
    goto error
)

echo [1/2] Installing build dependencies...
".venv\Scripts\python.exe" -m pip install -r requirements-dev.txt
if errorlevel 1 goto error

echo [2/2] Building translator.exe ...
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --distpath releases --workpath build-public translator.spec
if errorlevel 1 goto error
echo [OK] Output: %~dp0releases\translator.exe
echo Share only the executable, never translator_config.ini.
goto finish

:error
echo [ERROR] Build failed. See the message above.
set "RESULT=1"

:finish
if /i not "%~1"=="--no-pause" pause
exit /b %RESULT%
