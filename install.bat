@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"

rem Copyright (c) 2026 Nova Software. All rights reserved.
echo Copyright (c) 2026 Nova Software. All rights reserved.
echo.

where py >nul 2>nul
if not errorlevel 1 (
    set "PYTHON_COMMAND=py -3"
    !PYTHON_COMMAND! --version >nul 2>nul
    if errorlevel 1 set "PYTHON_COMMAND="
)

if not defined PYTHON_COMMAND (
    where python >nul 2>nul
    if not errorlevel 1 (
        set "PYTHON_COMMAND=python"
        !PYTHON_COMMAND! --version >nul 2>nul
        if errorlevel 1 set "PYTHON_COMMAND="
    )
)

if not defined PYTHON_COMMAND (
    echo Python 3 was not found. Install Python 3.10 or newer from https://www.python.org/downloads/
    echo Then run this installer again.
    pause
    exit /b 1
)

%PYTHON_COMMAND% -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul
if errorlevel 1 (
    %PYTHON_COMMAND% --version
    echo Python 3.10 or newer is required.
    pause
    exit /b 1
)

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -c "import sys, pip; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul
    if errorlevel 1 (
        echo Existing virtual environment is not usable on this computer. Recreating it...
        %PYTHON_COMMAND% -m venv --clear .venv
        if errorlevel 1 goto setup_error
    )
) else (
    %PYTHON_COMMAND% -m venv .venv
    if errorlevel 1 goto setup_error
)

".venv\Scripts\python.exe" -m pip --version >nul 2>nul
if errorlevel 1 goto setup_error

".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto setup_error

echo.
echo Installation completed. Start the program with run.bat.
pause
exit /b 0

:setup_error
echo.
echo Setup failed. Check your internet connection and confirm Python 3.10 or newer is installed.
pause
exit /b 1
