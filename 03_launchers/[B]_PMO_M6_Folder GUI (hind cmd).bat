@echo off
REM Portable: runs from 03_launchers, or from a copy anywhere once PMO_HOME is set
REM (setx PMO_HOME "<path to the Personal Media Organizer folder>").
set "dir_project=%~dp0.."
if not exist "%dir_project%\02_scripts" set "dir_project=%PMO_HOME%"
if not exist "%dir_project%\02_scripts" (
  echo Cannot find the project. Run this from 03_launchers, or set PMO_HOME once:
  echo   setx PMO_HOME "<path to the Personal Media Organizer folder>"
  pause
  exit /b 1
)
cd /d "%dir_project%"
start "" "C:\Program Files\Python310\pythonw.exe" "PersonalMediaOrganizer\M8_Folder GUI.py"
exit
