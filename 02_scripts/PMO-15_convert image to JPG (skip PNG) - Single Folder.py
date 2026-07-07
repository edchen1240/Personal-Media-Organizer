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
from PIL import UnidentifiedImageError, Image
from tkinter.filedialog import askdirectory

import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PersonalMediaOrganizer import M1_Files as M1F
from PersonalMediaOrganizer import M3_Image as M3I


#[1] Ask folder location
#dir_sort = r'D:\01_Floor\a_Ed\17_Preschool\02_字卡\02_圖片前處理' # It's connected with bat files. Don't change.
#dir_sort, bsn_dir = MD1U.tkinter_select_directory(dialog_title='Select a directory')
#dir_sort = os.getcwd()     # Remove this line when fixing the code in VC code.

def check_directory_exists(dir_path):
    if os.path.isdir(dir_path):
        print(f'The directory exists: {dir_path}.')
        return True
    else:
        print(f'The directory does not exist: {dir_path}.')
        return False

#[2] Get the directory path from the command-line arguments
if len(sys.argv) < 2:
    message = (
        f"\nlen(sys.argv) = {len(sys.argv)}. sys.argv = {sys.argv}.\n"
        "This code is designed to be run from the terminal using a batch file and requires an input argument (typically a directory address).\n"
        "Please run the code using the batch file (.bat), or comment out this check if you are running it in a different environment.\n"
    )
    print(message)
    raise ValueError(message)
    sys.exit()

dir_sort = sys.argv[1].rstrip('\"').rstrip('/')      
check_directory_exists(dir_sort)

#dir_sort = r'D:\01_Floor\a_Ed\11_Maker\18_Fridge Magnet\03_FM_Photo waiting'

#[3] Check directory.
print(f'\nCurrent directory: {dir_sort}')

#[5] Dump AAE fils.
list_paths, list_bsn = M1F.batch_file_relocate(dir_sort, ['.AAE'], [], '01_AAE', print_bsn=False)

#[6] Convert HEIC, WEBP, and AVIF to JPG.
list_path_JPG, list_error = M3I.convert_image_to_jpg_ignore_PNG(dir_sort, 
                                                                delete_original=False, 
                                                                print_status=True, 
                                                                dump_dir_name='02_Originals')


#[7] Remove duplicates
list_dup_split = [' (', ' - Copy']
dup_folder='03_Dup'
list_path_main_name = M3I.move_duplicate_files_in_dir(dir_sort, list_dup_split, dup_folder)


print('\nCompleted. Close in 5 seconds.')
time.sleep(5)

