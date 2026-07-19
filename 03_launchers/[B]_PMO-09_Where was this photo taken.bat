@echo off
:loop

cd /d "%~dp0..\02_scripts"
python "PMO-09_Where was this photo taken.py"

echo.
echo Press ENTER to run again, or Ctrl+C to exit.
pause >nul
goto loop
