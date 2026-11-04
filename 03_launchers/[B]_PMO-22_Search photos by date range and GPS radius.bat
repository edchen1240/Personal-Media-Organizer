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
:loop

REM --- Run options. Edit this one line; empty means the script's defaults.
REM     Example: set "ARGS=--date-start 2019-06-01 --date-end 2019-06-30 --radius-m 500"
set "ARGS="

cd /d "%dir_project%\02_scripts"
python "PMO-22_Search photos by date range and GPS radius.py" %ARGS%

echo.
echo Press ENTER to run again, or Ctrl+C to exit.
pause >nul
goto loop
