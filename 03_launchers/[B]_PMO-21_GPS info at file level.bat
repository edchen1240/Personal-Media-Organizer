@echo off
:loop
cd /d "%~dp0..\02_scripts"
python "PMO-21_GPS info at file level.py"
pause
goto loop
