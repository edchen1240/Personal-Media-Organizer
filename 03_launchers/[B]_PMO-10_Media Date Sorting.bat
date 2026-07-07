@echo off
:loop
cd /d "%~dp0..\02_scripts"
python "PMO-10_Media Date Sorting.py"
pause
goto loop
