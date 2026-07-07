"""
[MDS_M4_Classes]
Purpose: Check the device for the LMS system.
Author: Meng-Chi Ed Chen
Date: 2024-0613

Status: Complete.
"""
import os, sys, time, glob, re, cv2, shutil
from datetime import datetime, timedelta
from tabulate import tabulate
from tkinter.filedialog import askdirectory
import numpy as np

import os, sys, time
from PersonalMediaOrganizer import M1_Files as M1F
from PersonalMediaOrganizer import M3_Image as M3I
import pandas as pd






class FileLevelGPSInfoExport:
    
    """
    
    
    Full execution flow: 
    __init__
        └─ validate_date_range_and_confirm()
            ├─ resolves date_start/date_end
            ├─ collects self.list_path
            └─ "Do you want to continue?" → user confirms
        └─ run()                          ← fires immediately after confirm
            ├─ loops every file: datetime + GPS + city → df_gps row
            └─ save_df_gps_to_excel()    → Excel + open folder

    
    """
    
    
    def __init__(   self, 
                    dir_work,
                    date_start,
                    date_end,
                    dir_output,
                    city_name = False
                    ):

        #[1] Regist instance variables.
        self.dir_work = dir_work
        self.date_start = date_start
        self.date_end = date_end
        self.dir_output = dir_output
        self.city_name = city_name
        self.cnt_date_search = 3
        
        
        #[5] Allowed file extensions. (We stick to JPG for now.)
        self.list_ext_allowed = ['.jpg', '.jpeg'] 
        
        #[6] Excel settings.
        self.bsn_xlsx = f'GPS Info_{self.date_start}~{self.date_end}.xlsx'
        self.col_df_gps = ['File Name', 'Date Taken', 'Time Taken', 'Latitude', 'Longitude', 'Location Name', 'Note']
        self.df_gps = pd.DataFrame(columns=self.col_df_gps)
        # Note column left empty for user.

        #[7] Validate date range, confirm with user, then run.
        self.validate_date_range_and_confirm()
        self.run()


    def find_nearest_date_folder(self, target_date_str):
        target = datetime.strptime(target_date_str, '%Y-%m-%d')
        for delta in range(self.cnt_date_search + 1):
            for offset in ([0] if delta == 0 else [delta, -delta]):
                folder = (target + timedelta(days=offset)).strftime('%Y-%m-%d')
                if os.path.isdir(os.path.join(self.dir_work, folder)):
                    return folder
        raise FileNotFoundError(
            f'No date folder found within ±{self.cnt_date_search} days of {target_date_str} in {self.dir_work}.'
        )


    def validate_date_range_and_confirm(self):
        #[1] Resolve date_start and date_end to nearest existing date folders.
        self.date_start = self.find_nearest_date_folder(self.date_start)
        self.date_end   = self.find_nearest_date_folder(self.date_end)
        print(f'-- Resolved date range: [{self.date_start}, {self.date_end}]')

        #[2] Collect image files from each date folder within the range.
        list_path = []
        all_subdirs = sorted([
            d for d in os.listdir(self.dir_work)
            if os.path.isdir(os.path.join(self.dir_work, d))
            and re.match(r'^\d{4}-\d{2}-\d{2}$', d)
            and self.date_start <= d <= self.date_end
        ])
        for subdir in all_subdirs:
            files, _ = M1F.filter_files_by_extension(
                os.path.join(self.dir_work, subdir),
                list_ext           = self.list_ext_allowed,
                include_or_exclude = 'include',
                remove_file        = False
            )
            list_path.extend(files)

        if not list_path:
            raise FileNotFoundError(
                f'No {self.list_ext_allowed} files found in date range [{self.date_start}, {self.date_end}].'
            )

        self.list_path = list_path
        cnt_in_range = len(self.list_path)
        print(f'-- Files in range [{self.date_start}, {self.date_end}]: {cnt_in_range}')

        #[3] Ask user if they want to continue.
        str_continue = M1F.ask_for_input(
            f'Found {cnt_in_range} files. Do you want to continue? (Close the program to exit):\n',
            readback=True, allow_empty=False
        )
        if str_continue.lower() not in ['y', 'yes', 'yeah', 'ok', 'okey', 'aff', 'affirmative']:
            print('No affirmative answer detected. Exiting...')
            sys.exit(0)


    def run(self):
        cnt_total = len(self.list_path)
        print(f'\n[run] Extracting GPS info from {cnt_total} files...')

        list_rows = []
        for i, path_img in enumerate(self.list_path):
            bsn = os.path.basename(path_img)
            t_1 = time.time()

            #[1] Get date and time taken.
            _, datetime_str, _ = M3I.retrieve_datetime_of_single_media_files(path_img, '%Y-%m-%d, %H:%M:%S')
            if datetime_str:
                date_taken, time_taken = datetime_str.split(', ')
            else:
                date_taken, time_taken = None, None

            #[2] Get GPS coordinates and city name.
            lat_deg, lon_deg, str_city = M3I.extract_latitude_and_longitude_from_path_img(path_img, city_name=self.city_name)

            #[3] Collect row into list — build DataFrame once after loop (avoids O(n²) concat).
            list_rows.append({'File Name':     bsn,
                              'Date Taken':    date_taken,
                              'Time Taken':    time_taken,
                              'Latitude':      lat_deg,
                              'Longitude':     lon_deg,
                              'Location Name': str_city,
                              'Note':          ''})
            t_2 = time.time()
            print(f'-- [{i+1:04d}/{cnt_total:04d}] {bsn} \t| {date_taken} \t| {str_city} \t| {t_2-t_1:.2f} sec')

        #[4] Build DataFrame once from collected rows.
        self.df_gps = pd.DataFrame(list_rows, columns=self.col_df_gps)

        #[5] Save results to Excel.
        self.save_df_gps_to_excel()




    def save_df_gps_to_excel(self):
        #[1] Ensure output directory exists.
        os.makedirs(self.dir_output, exist_ok=True)

        #[2] Save df_gps to Excel.
        sheet_name = 'GPS Info'
        path_xlsx  = os.path.join(self.dir_output, self.bsn_xlsx)
        M1F.save_df_as_excel_add_with_full_path(self.df_gps, path_xlsx, sheet_name)

        #[3] Adjust column widths.
        #    (A=index), B=File Name, C=Date Taken, D=Time Taken,
        #    E=Latitude, F=Longitude, G=Location Name, H=Note
        list_column_letters = ['A', 'B', 'C', 'D', 'E',  'F',  'G',  'H']
        list_column_widths  = ['5', '30','14','12','14', '14', '25', '30']
        M1F.adjust_multiple_column_widths(path_xlsx, sheet_name, list_column_letters, list_column_widths)

        #[4] Open output folder.
        M1F.open_a_folder_on_windows(self.dir_output)
        print(f'-- GPS info saved to: {path_xlsx}')
