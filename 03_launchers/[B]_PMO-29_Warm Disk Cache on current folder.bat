@echo off
REM Usage 1: drag-and-drop a folder onto this .bat to warm that folder.
REM Usage 2: copy this .bat into a folder and double-click to warm that folder
REM          (requires editing dir_project below if the project ever moves).
if "%~1"=="" (set "dir_target=%~dp0") else (set "dir_target=%~1")

set "dir_project=%~dp0.."
if not exist "%dir_project%\02_scripts" set "dir_project=D:\01_Floor\a_Ed\09_EECS\10_Python\05_Complete\2022-0603_Personal Media Organizer"

cd /d "%dir_project%"
python "02_scripts\PMO-29_Warm Disk Cache on current folder.py" "%dir_target%"

echo.
echo Press ENTER to close.
pause >nul
