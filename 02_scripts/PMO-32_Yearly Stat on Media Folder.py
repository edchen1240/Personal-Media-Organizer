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
from PersonalMediaOrganizer import M0_Configuration as M0C
from PersonalMediaOrganizer import M1_Files as M1F
from PersonalMediaOrganizer import M3_Image as M3I
from PersonalMediaOrganizer import M5_Statistics as M5S





M5S.MediaFolderOverview(M0C.DIR_MEDIA, M0C.DIR_OUTPUT)

















sys.exit('The following function-like script is awaiting integration. 2026-0715-2143.')




#[1] Ask folder location
print('\nWelcome to Media Date Sorting.\nLet us turn your mements into memories.')
dir_memory = r'D:\01_Floor\b_Memory\01_DailyPhotosVedios_2021-2030'
dir_report = r'D:\01_Floor\a_Ed\09_EECS\10_Python\05_Complete\2022-0603_Personal Media Organizer\PMO-12_Yearly Stat Report'
print(f'Please make sure the directories are set correctly.\ndir_memory: \t{dir_memory}\ndir_report: \t{dir_report}')


#[3] Ask folder keyword.
question_message = '\nWhat keyword would you like to search for in the folder name? \n'\
                    'For example, year (2014-), specific month (2014-07), or specific date (2014-07-05).\n'
kwd_folder = M1F.ask_for_input(question_message, readback=True, allow_empty=True)

#[3] Filter folder.
list_kwd_yes_or_1 = [kwd_folder]
list_kwd_no_or_2 = []
list_dirs, list_bsns = M1F.filter_folders_in_dir_with_keywords(dir_memory, list_kwd_yes_or_1, list_kwd_no_or_2, print_bsn = True)

#[10] Start text name.
timestamp = datetime.now().strftime("%Y-%m%d-%H%M%S")
path_xlsx = os.path.join(dir_report, f'{kwd_folder}_Media Stat_{timestamp}.xlsx')

#[15] Generate statistics for a list of directories.
df_folders =  M1F.batch_folder_file_stat(list_dirs)
sheet_name = 'Media stat'
M1F.save_df_as_excel_overwrite(df_folders, path_xlsx, sheet_name)
list_column_letters = ['B', 'C', 'D', 'E', 'F', 'G']
list_column_widths = ['20', '20', '20', '20', '20', '20']
M1F.adjust_multiple_column_widths(path_xlsx, sheet_name, list_column_letters, list_column_widths)

#[16] Open the folder to see the report.
M1F.open_a_folder_on_windows(dir_report)

#[20] Complete
print('\nCompleted. Close in 5 seconds.')
time.sleep(5)
