"""
[PMO-30_Warm Disk Cache on Media Folder.py]
Purpose: Pre-read file metadata of DIR_MEDIA into the Windows cache so that
         PMO-31 (coarse statistics) and File Explorer stay fast and responsive.
Author: Meng-Chi Ed Chen
Date: 2026-07-16

How it works:
    1. Runs in Windows "background mode" (lowest I/O priority), so it never
       starves File Explorer or other programs — it only uses idle disk time.
    2. Walks every folder single-threaded and stats every file. This pulls
       the NTFS metadata (names, sizes) into RAM cache.
    3. After it finishes, any metadata scan of the same tree (e.g. PMO-31)
       reads from RAM instead of the disk and completes in seconds.

Usage: Run this first (or leave it running in the background), then run PMO-31.

Status: Complete.
"""
import os, sys, time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PersonalMediaOrganizer import M0_Configuration as M0C
from PersonalMediaOrganizer import M6_System as M6S


#[1] Opening message.
text_msg = '\n==============================\n'\
            'PMO-30: Warm Disk Cache on Media Folder\n'\
            '==============================\n'\
            f'Welcome to PMO-30_Warm Disk Cache on Media Folder.py.\n'\
            f'- This script pre-reads file metadata of DIR_MEDIA into the Windows cache:\n'\
            f'  {M0C.DIR_MEDIA}\n'\
            '- It runs in Windows "background mode" (lowest I/O priority), so it never starves File Explorer or other programs — it only uses idle disk time.\n'\
            '- It walks every folder single-threaded and stats every file. This pulls the NTFS metadata (names, sizes) into RAM cache.\n'\
            '- After it finishes, any metadata scan of the same tree (e.g. PMO-31) reads from RAM instead of the disk and completes in seconds.\n'\
            '- Usage: Run this first (or leave it running in the background), then run PMO-31.\n'
print(text_msg)


#[2] Warm disk cache.
M6S.enter_background_mode()
M6S.warm_folder_metadata(M0C.DIR_MEDIA)
print('\nCompleted. You can now run PMO-31. Close in 5 seconds.')
time.sleep(5)
