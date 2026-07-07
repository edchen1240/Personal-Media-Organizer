@echo off
:loop
cd /d "%~dp0..\02_scripts"
python "PMO-08_[Reset] move all filles up.py"
pause
goto loop
