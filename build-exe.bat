@echo off
setlocal
cd /d "%~dp0"

rem Copyright (c) 2026 Nova Software. All rights reserved.
echo Copyright (c) 2026 Nova Software. All rights reserved.
echo.

if not exist ".venv\Scripts\python.exe" (
    echo Runtime environment not found. Run install.bat first.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" -c "import PyInstaller" >nul 2>nul
if errorlevel 1 (
    ".venv\Scripts\python.exe" -m pip install pyinstaller
    if errorlevel 1 goto build_error
)

".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --onefile --console --name NovaSoftware --paths src --specpath build --workpath build\pyinstaller --distpath dist --add-data "%CD%\config.ini;." --collect-all dxcam --hidden-import mouse.interception_mouse --hidden-import mouse.microcontroller_serial_mouse --hidden-import mouse.microcontroller_socket_mouse --hidden-import win32cred --hidden-import win32timezone --hidden-import pywintypes --hidden-import win32api --hidden-import win32con src\main.py
if errorlevel 1 goto build_error

echo.
echo Build completed: dist\NovaSoftware.exe
pause
exit /b 0

:build_error
echo.
echo Build failed. Review the error above.
pause
exit /b 1
