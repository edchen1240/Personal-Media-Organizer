"""
[PMO-08_move all directory one level up.py]
Purpose: Quickly restore files test folder.
Author: Meng-Chi Ed Chen
Date: 2022-06-10
Reference:
    1.https://stackoverflow.com/questions/8858008/how-to-move-a-file-in-python
    2.
"""


import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PersonalMediaOrganizer import M1_Files as M1F


#[1] Get the directory path from the command-line arguments
dir_sort = M1F.get_working_dir_from_sysargv()

#[1] Ask folder location
#dir_sort = askdirectory(title='Select Folder')

#[2] Move all files one level up.
M1F.move_all_files_in_the_subdirs_into_main_dir(dir_sort, print_status=True)
    
