"""
[PMO-29_Warm Disk Cache on current folder.py]
Purpose: Pre-read file metadata of a chosen folder into the Windows cache so
         that browsing and scanning that folder stays fast and responsive.
Author: Meng-Chi Ed Chen
Date: 2026-07-16

How it works:
    1. Runs in Windows "background mode" (lowest I/O priority), so it never
       starves File Explorer or other programs — it only uses idle disk time.
    2. Walks every folder single-threaded and stats every file. This pulls
       the NTFS metadata (names, sizes) into RAM cache.
    3. After it finishes, any metadata scan of the same tree reads from RAM
       instead of the disk and completes in seconds.

Usage: Launch via [B]_PMO-29 (warms the project folder), or pass any folder
       path as the first command-line argument.

Status: Complete.
"""
import os, sys, time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PersonalMediaOrganizer import M6_System as M6S
from PersonalMediaOrganizer import M1_Files as M1F


#[1] Get the directory path from the command-line arguments.
dir_work, dir_bsn = M1F.get_working_dir_from_sysargv()

#[2] Opening message.
text_msg = '\n==============================\n'\
            'PMO-29: Warm Disk Cache on current folder\n'\
            '==============================\n'\
            f'Welcome to PMO-29_Warm Disk Cache on current folder.py.\n'\
            f'- This script pre-reads file metadata of the folder below into the Windows cache:\n'\
            f'  {dir_work}\n'\
            '- It runs in Windows "background mode" (lowest I/O priority), so it never starves File Explorer or other programs — it only uses idle disk time.\n'\
            '- It walks every folder single-threaded and stats every file. This pulls the NTFS metadata (names, sizes) into RAM cache.\n'\
            '- After it finishes, browsing and scanning this folder reads from RAM instead of the disk.\n'
print(text_msg)


#[3] Warm disk cache.
M6S.enter_background_mode()
M6S.warm_folder_metadata(dir_work)
print('\nCompleted. This folder is now cached and will browse fast. Close in 5 seconds.')
time.sleep(5)
