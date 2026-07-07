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
#dir_sort, bsn_dir = M3I.tkinter_select_directory(dialog_title='Select a directory')
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


#[3] Check directory.
print(f'\nCurrent directory: {dir_sort}')

#[5] Dump AAE fils.
list_paths, list_bsn = M1F.batch_file_relocate(dir_sort, ['.AAE'], [], '01_AAE', print_bsn=False)

#[6] Convert HEIC, WEBP, and AVIF to JPG.
list_path_JPG_JEPG, list_error_JEPG = M3I.replace_JPEG_to_JPG(dir_sort)
list_path_JPG_HEIC, list_error_HEIC = M3I.convert_HEIC_to_JPG_and_keep_EXIF_info(dir_sort, 
                                                                                  delete_or_remove=False, 
                                                                                  print_status=True, 
                                                                                  dump_dir_name='02_HEIC (processed)')
list_path_JPG_WEBP, list_error_WEBP = M3I.convert_WEBP_to_JPG_and_keep_EXIF_info(dir_sort, 
                                                                                  delete_or_remove=False, 
                                                                                  print_status=True, 
                                                                                  dump_dir_name='03_WEBP (processed)')
list_path_JPG_AVIF, list_error_AVIF = M3I.convert_AVIF_to_JPG_and_keep_EXIF_info(dir_sort, 
                                                                                  delete_or_remove=False, 
                                                                                  print_status=True, 
                                                                                  dump_dir_name='04_AVIF (processed)')

list_path_JPG_TIFF, list_error_TIFF = M3I.convert_TIFF_to_JPG_and_keep_EXIF_info(dir_sort, 
                                                                                  delete_or_remove=False, 
                                                                                  print_status=True, 
                                                                                  dump_dir_name='05_TIFF (processed)')

list_path_JPG = list_path_JPG_JEPG + list_path_JPG_HEIC + list_path_JPG_WEBP + list_path_JPG_AVIF
list_error = list_error_JEPG + list_error_HEIC + list_error_WEBP + list_error_AVIF





#[7] Remove duplicates.
list_dup_split = [' (', ' - Copy']
dup_folder='03_Dup'
list_path_main_name = M3I.move_duplicate_files_in_dir(dir_sort, list_dup_split, dup_folder)

#[8] Rotate image.
#list_path_rotated = M3I.rotate_image_files_upright(dir_sort)

print('\nCompleted. Close in 5 seconds.')
time.sleep(5)

