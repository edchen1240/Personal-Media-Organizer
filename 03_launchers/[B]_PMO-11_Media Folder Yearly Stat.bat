@echo off
:loop
cd /d "%~dp0..\02_scripts"
python "PMO-11_Media Folder Yearly Stat.py"
pause
goto loop
