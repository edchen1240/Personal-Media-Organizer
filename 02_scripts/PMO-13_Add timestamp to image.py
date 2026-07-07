"""
[PMO-12_Add date to the file name.py]
Purpose: Get "date taken" of photos and videos.
Author: Meng-Chi Ed Chen
Date: 2022-06-11
Notes:
2025-1116-1228: Update "get_working_dir_from_sysargv" and "check_folder_and_reset_files" functions in MDS_M1_Files.py.

Status: Final complete version.
"""

import os, sys, time, glob, cv2

import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PersonalMediaOrganizer import M1_Files as M1F
from PersonalMediaOrganizer import M3_Image as M3I
from PersonalMediaOrganizer import M4_Classes as M4C



#[1] Get the directory path from the command-line arguments
dir_work, dir_bns = M1F.get_working_dir_from_sysargv()

#[2] Main process: Add timestamp to images.
M4C.AddTimestampManager(dir_work,
                        dt_source           = 'cross_check',
                        location            = 'top-left',
                        put_on_padding      = True)


#[15] Complete.
print('\nCompleted. Close in 5 seconds.')
time.sleep(5)





