@echo off
:loop
cd /d "%~dp0.."
python "02_scripts\PMO-18_Fix Image Files.py"
pause
goto loop
