@echo off
setlocal
cd /d "%~dp0"
echo == Python launcher ==
py -0p 2>nul
echo == Python on PATH ==
where python 2>nul
if exist ".venv\Scripts\python.exe" (
    echo == Project environment ==
    ".venv\Scripts\python.exe" --version
    ".venv\Scripts\python.exe" -m pip check
) else (
    echo [INFO] No project environment. Run setup.bat first.
)
if /i not "%~1"=="--no-pause" pause
