@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo   PM 智投 · 正在启动...
echo ============================================

REM 优先使用本机 WorkBuddy 受管 venv 中的 Python；否则回退到系统 python
set "VENV_PY=%USERPROFILE%\.workbuddy\binaries\python\envs\default\Scripts\python.exe"
if exist "%VENV_PY%" (
    set "PY=%VENV_PY%"
) else (
    set "PY=python"
)
echo 使用 Python: %PY%

REM 首次运行自动安装依赖
"%PY%" -c "import fastapi, uvicorn, pypdf, docx, httpx" >nul 2>&1
if errorlevel 1 (
    echo [首次运行] 正在安装依赖...
    "%PY%" -m pip install -r requirements.txt
)

"%PY%" main.py
pause
