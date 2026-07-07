@echo off
set "dir_current=%~dp0"
cd /d "%~dp0.."
python "02_scripts\PMO-01_Single Media Folder Cleaning.py" "%dir_current%"
exit
