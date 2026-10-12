@echo off
REM Usage 1: drag-and-drop a folder onto this .bat to warm that folder.
REM Usage 2: copy this .bat into a folder and double-click to warm that folder
REM          (needs the PMO_HOME environment variable, set once with
REM          setx PMO_HOME "<path to the Personal Media Organizer folder>").
if "%~1"=="" (set "dir_target=%~dp0") else (set "dir_target=%~1")

set "dir_project=%~dp0.."
if not exist "%dir_project%\02_scripts" set "dir_project=%PMO_HOME%"
if not exist "%dir_project%\02_scripts" (
  echo Cannot find the project. Run this from 03_launchers, or set PMO_HOME once:
  echo   setx PMO_HOME "<path to the Personal Media Organizer folder>"
  pause
  exit /b 1
)

cd /d "%dir_project%"
python "02_scripts\PMO-29_Warm Disk Cache on current folder.py" "%dir_target%"

echo.
echo Press ENTER to close.
pause >nul
