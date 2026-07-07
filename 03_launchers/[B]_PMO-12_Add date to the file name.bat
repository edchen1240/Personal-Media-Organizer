@echo off
:loop
cd /d "%~dp0..\02_scripts"
python "PMO-12_Add date to the file name.py"
pause
goto loop
