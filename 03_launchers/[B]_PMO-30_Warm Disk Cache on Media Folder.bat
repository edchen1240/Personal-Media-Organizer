@echo off
:loop

cd /d "%~dp0..\02_scripts"
python "PMO-30_Warm Disk Cache on Media Folder.py"

echo.
echo Press ENTER to run again, or Ctrl+C to exit.
pause >nul
goto loop
