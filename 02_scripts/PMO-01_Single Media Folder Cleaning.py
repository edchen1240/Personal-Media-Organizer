"""
[PMO-01_Single Media Folder Cleaning.py]
Purpose: Get "date taken" of photos and videos.
Author: Meng-Chi Ed Chen
Date: 2025-11-15.
Notes:
2025-1115-0902: Want to improve into class structure, but might take time.
2025-1116-1230: Upadte "get_working_dir_from_sysargv" and "check_folder_and_reset_files" functions in MDS_M1_Files.py. Good for now.
    
    
Status: Complete.

"""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PersonalMediaOrganizer import M1_Files as M1F
from PersonalMediaOrganizer import M3_Image as M3I




#[1] Get the directory path from the command-line arguments
dir_current, dir_bns = M1F.get_working_dir_from_sysargv()

#[2] Reset files from previous runs if needed.
kwd_test_run_folder = ['01_AAE', '03_Dup']
exit_after_reset = True
M1F.check_folder_and_reset_files(dir_current, 
                                 kwd_test_run_folder    = kwd_test_run_folder, 
                                 exit_after_reset       = exit_after_reset)


#[3] Dump AAE fils.
list_paths, list_bsn = M1F.batch_file_relocate(dir_current, ['.AAE'], [], '01_AAE', print_bsn=False)

#[5] Convert HEIC to JPG.
list_path_JPG, list_error_HEIC = M3I.convert_HEIC_to_JPG_and_keep_EXIF_info(dir_current, 
                                                                            delete_or_remove=False, 
                                                                            print_status=True, 
                                                                            dump_dir_name='02_HEIC (processed)')

#[4] Remove duplicates
list_dup_split = [' (', ' - Copy']
dup_folder='03_Dup'
list_path_main_name = M3I.move_duplicate_files_in_dir(dir_current, list_dup_split, dup_folder)
print('\n[list_path_main_name]:\n' + '\n'.join(list_path_main_name))

#[20] Complete
print('\nCompleted. Close in 5 seconds.')
time.sleep(5)

