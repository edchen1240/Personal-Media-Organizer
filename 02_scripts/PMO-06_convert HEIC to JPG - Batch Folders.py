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
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PersonalMediaOrganizer import M1_Files as M1F
from PersonalMediaOrganizer import M3_Image as M3I



#[1] Choose batch or single mode.
batch_or_single = 'batch'  #'single' or 'batch'
if batch_or_single == 'single':
    dir_current, dir_bns = M1F.get_working_dir_from_sysargv()
    list_dir = [dir_current]
else:
    parent_dir = r'D:\01_Floor\b_Memory\01_DailyPhotosVedios_2011-2020'
    folder_kwd = '2019-02-2'
    list_dir = [os.path.join(parent_dir, d) for d in os.listdir(parent_dir) if folder_kwd in d and os.path.isdir(os.path.join(parent_dir, d))]


#[3] Process each folder.
cnt_total = len(list_dir)
for i, iter_path in enumerate(list_dir):
    iter_bsn_ext = os.path.basename(iter_path)
    print(f'\n[{+1:03}/{cnt_total:03}] {iter_bsn_ext}')

    #[2] Dump AAE fils.
    list_paths, list_bsn = M1F.batch_file_relocate(iter_path, ['.AAE'], [], '01_AAE', print_bsn=False)

    #[3] Convert HEIC to JPG.
    list_path_JPG, list_error_HEIC \
        = M3I.convert_HEIC_to_JPG_and_keep_EXIF_info(iter_path, 
                                                    delete_or_remove=False, 
                                                    print_status=True, 
                                                    dump_dir_name='02_HEIC (processed)')

    #[4] Remove duplicates.
    list_dup_split = [' (', ' - Copy']
    dup_folder='03_Dup'
    list_path_main_name = M3I.move_duplicate_files_in_dir(iter_path, list_dup_split, dup_folder)

    #[5] Rotate image.
    #list_path_rotated = MD1U.rotate_image_files_upright(iter_path)


print(f'Complete {i+1} folders. Close in 5 seconds.')


