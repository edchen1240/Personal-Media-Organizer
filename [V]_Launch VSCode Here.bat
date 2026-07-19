@echo off
REM Open VS Code at the folder where this batch script is located.
start "" "C:\Program Files\Microsoft VS Code\Code.exe" "%~dp0"
REM Change "%~dp0" to other fixed directory if you need to relocated this script.