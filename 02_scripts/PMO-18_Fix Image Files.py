"""
[PMO-18_Fix Image Files.py]
Purpose: Get "date taken" of photos and videos.
Author: Meng-Chi Ed Chen
Date: 2022-06-11
Reference:
    1.https://thispointer.com/python-get-list-of-files-in-directory-sorted-by-date-and-time/
    2.

Status: Final complete version.
"""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PersonalMediaOrganizer import M1_Files as M1F
from PersonalMediaOrganizer import M3_Image as M3I
from PersonalMediaOrganizer import M4_Classes as M4C

#[2] Get the directory path from the command-line arguments
list_path_file, list_bsn_file = M1F.tkinter_select_multiple_files(dialog_title='Select files', allow_close=False)

M3I.fix_corrupted_image_files(list_path_file, None, True)

#[15] Complete.
print('\nCompleted. Close in 5 seconds.')
time.sleep(5)





