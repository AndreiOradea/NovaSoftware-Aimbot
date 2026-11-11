@echo off
setlocal
cd /d "%~dp0"
set "NOVA_KEYGEN_ACCOUNT_ID=6d08df46-47ac-4078-9460-67d68a495d3f"

rem Copyright (c) 2026 Nova Software. All rights reserved.

color 0D
echo.
echo    #   #   ###   #   #   ###   
echo    ##  #  #   #  #   #  #   #  
echo    # # #  #   #  #   #  #   #  
echo    #  ##  #   #  #   #  #####  
echo    #   #  #   #   # #   #   #  
echo    #   #  #   #   # #   #   #  
echo    #   #   ###     #    #   #  
echo.
echo     ####   ###   #####  #####  #   #    ###   ####   #####  
echo    #      #   #  #        #    #   #   #   #  #   #  #      
echo    #      #   #  #        #    #   #   #   #  #   #  #      
echo     ###   #   #  ####     #    # # #   #####  ####   ####   
echo        #  #   #  #        #    # # #   #   #  # #    #      
echo        #  #   #  #        #    ## ##   #   #  #  #   #      
echo    ####    ###   #        #    ## ##   #   #  #   #  #####  
echo.
echo Copyright (c) 2026 Nova Software. All rights reserved.
echo.

if not exist ".venv\Scripts\python.exe" (
    echo Runtime environment not found. Run install.bat first.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" src\main.py
set "exit_code=%ERRORLEVEL%"
echo.
echo Program stopped. Press any key to close this window.
pause >nul
exit /b %exit_code%
