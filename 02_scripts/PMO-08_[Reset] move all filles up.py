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
from PersonalMediaOrganizer import M0_Configuration as M0C
from PersonalMediaOrganizer import M1_Files as M1F


#[1] Default from argv (bat folder or drag-drop), else DIR_MEDIA. Then confirm or pick a subfolder by Index or pasted path.
#    Same pattern as PMO-12. The old code passed the (dir, basename) tuple straight into the mover, which cannot work.
if len(sys.argv) >= 2 and 'ipykernel_launcher.py' not in sys.argv[0]:
    default_dir, _ = M1F.get_working_dir_from_sysargv()
else:
    default_dir = M0C.DIR_MEDIA

dir_sort, dir_bsn = M1F.ask_for_directory(default_dir)

#[2] Move all files in the subfolders (one level down) up into the chosen folder.
M1F.move_all_files_in_the_subdirs_into_main_dir(dir_sort, print_status=True)

print('\nCompleted. Press ENTER to close.')
input()
    
