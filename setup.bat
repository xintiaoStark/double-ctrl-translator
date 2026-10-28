@echo off
setlocal
cd /d "%~dp0"
set "RESULT=0"

if exist ".venv\Scripts\python.exe" goto install

py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>&1
if not errorlevel 1 (
    py -3 -m venv .venv
    if errorlevel 1 goto error
    goto install
)

python -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Install Python 3.11 or newer from python.org first.
    goto error
)
python -m venv .venv
if errorlevel 1 goto error

:install
echo Installing dependencies into the project-local .venv ...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto error
echo [OK] Setup complete. Run start.bat or start_hidden.vbs.
goto finish

:error
echo [ERROR] Setup failed. See the message above.
set "RESULT=1"

:finish
if /i not "%~1"=="--no-pause" pause
exit /b %RESULT%
