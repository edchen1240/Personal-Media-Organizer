@echo off
set "dir_current=%~dp0"
cd /d "D:\01_Floor\a_Ed\09_EECS\10_Python\05_Complete\2024-0106_Batch File Rename"
python "BFR-13_Rename folders and files with find and replace.py" "%dir_current%"
exit