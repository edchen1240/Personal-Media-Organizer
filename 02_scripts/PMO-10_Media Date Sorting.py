"""
[PMO-06_Media Date Sorting.py]
Purpose: Get "date taken" of photos and videos.
Author: Meng-Chi Ed Chen
Date: 2022-06-11
Reference:
    1.https://thispointer.com/python-get-list-of-files-in-directory-sorted-by-date-and-time/
    2.

Status: Final complete version.
"""
import os, sys, time, glob
from datetime import datetime
from tabulate import tabulate
from tkinter.filedialog import askdirectory

import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PersonalMediaOrganizer import M1_Files as M1F
from PersonalMediaOrganizer import M3_Image as M3I
from PersonalMediaOrganizer import M4_Classes as M4C



#[2] Create MediaSortingManager instance
MSM = M4C.MediaSortingManager()
MSM.dump_AAE_files()
MSM.convert_HEIC_to_JPG()
MSM.filter_media_files()
MSM.organize_files_by_date()
MSM.search_large_files(mb_limit=10)
MSM.save_report()

print('\nCompleted. Close in 5 seconds.')
time.sleep(5)






