"""
[PMO-12_Add date to the file name.py]
Purpose: Get "date taken" of photos and videos.
Author: Meng-Chi Ed Chen
Date: 2022-06-11
Notes:
2025-1116-1228: Update "get_working_dir_from_sysargv" and "check_folder_and_reset_files" functions in MDS_M1_Files.py.
2026-08-10: Confirm/pick folder via ask_for_directory (argv or DIR_MEDIA as default; Index or pasted path).

Status: Final complete version.
"""

import os, sys, time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PersonalMediaOrganizer import M0_Configuration as M0C
from PersonalMediaOrganizer import M1_Files as M1F
from PersonalMediaOrganizer import M4_Classes as M4C


#[1] Default from argv (bat / drag-drop); else DIR_MEDIA. Then confirm or pick a subfolder.
if len(sys.argv) >= 2 and 'ipykernel_launcher.py' not in sys.argv[0]:
    default_dir, _ = M1F.get_working_dir_from_sysargv()
else:
    default_dir = M0C.DIR_MEDIA

dir_work, dir_bsn = M1F.ask_for_directory(default_dir)


M4C.AddDateToFileNameManager(dir_work)








#[15] Complete.
print('\nCompleted. Close in 5 seconds.')
time.sleep(5)
