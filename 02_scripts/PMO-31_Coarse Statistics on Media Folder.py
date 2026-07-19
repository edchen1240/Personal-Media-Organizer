"""
[PMO-31_Coarse Statistics on Media Folder.py]
Purpose: Folder-level statistics of DIR_MEDIA (counts, sizes) with Excel
         report and chart. Can rerun the scan or replot from a saved report.
Author: Meng-Chi Ed Chen
Date: 2026-07-16

Status: Complete.
"""
import os, sys, time, glob
from datetime import datetime
from tabulate import tabulate
from tkinter.filedialog import askopenfilename

import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PersonalMediaOrganizer import M0_Configuration as M0C
from PersonalMediaOrganizer import M1_Files as M1F
from PersonalMediaOrganizer import M3_Image as M3I
from PersonalMediaOrganizer import M5_Statistics as M5S


def locate_the_latest_excel_report(dir_output, prefix='Media Folder Stat_', suffix='.xlsx'):
    """Locate the latest Excel report in the output directory."""
    list_xlsx = glob.glob(os.path.join(dir_output, f'{prefix}*{suffix}'))
    if not list_xlsx:
        return None
    path_latest_file = max(list_xlsx, key=os.path.getmtime)
    return path_latest_file




#[1] Ask to regenerate statistics or read from existing Excel file.
text_q1 =   f'\n'\
            f'==================================================\n'\
            f'PMO-31_Coarse Statistics on Media Folder.py\n'\
            f'==================================================\n'\
            f'Wecome to PMO-31_Coarse Statistics on Media Folder.py. Would you like to:\n'\
            f'(A) Run new statistics on the media folder (this may take a while), or\n'\
            f'(B) Read from the existing Excel file and regenerate plots (much faster)?\n'\
            f'Please enter A or B:\n'
text_a1 = M1F.ask_for_input(text_q1, False, False).strip().upper()

if text_a1 == 'A':
    print(f'\nRunning new statistics on the media folder (this may take a while)...')
    #[2] Scan → summarize → save Excel (both sheets) → plot.
    MFO = M5S.MediaFolderOverview(M0C.DIR_MEDIA, M0C.DIR_OUTPUT)
    MFO.scan_media_folders()
    MFO.calculate_statistics_summary()
    MFO.save_stat_result_to_excel()
    MFO.plot_scan_media_folders()
    
    
elif text_a1 == 'B':
    print(f'\nReading from the existing Excel file and regenerating plots.')
    
    #[3] Ask for path to the existing Excel report.
    text_a2 = False
    path_latest_xlsx = locate_the_latest_excel_report(M0C.DIR_OUTPUT)
    if path_latest_xlsx is not None:
        text_q2 = f'Is this the correct Excel report to read from?\n{path_latest_xlsx}\nPlease enter Y or N:\n'
        text_a2 = M1F.question_and_if_yes_action(text_q2)
    
    #[4] If not, ask user to select the Excel report.
    if text_a2 is False:
        print(f'\nPlease select the Excel report (or cancel to exit).')
        path_latest_xlsx = askopenfilename(
            title      = 'Select the Excel report',
            initialdir = M0C.DIR_OUTPUT,
            filetypes  = [('Excel files', '*.xlsx')])
        if not path_latest_xlsx:
            sys.exit('No Excel report selected. Exiting.')
    
    #[5] Read sheet 2_statistics → rebuild 1_metadata → save metadata only → plot.
    MFO = M5S.MediaFolderOverview(M0C.DIR_MEDIA, M0C.DIR_OUTPUT)
    MFO.read_stat_result_from_excel(path_latest_xlsx)
    MFO.calculate_statistics_summary()
    MFO.save_stat_result_to_excel(path_xlsx=path_latest_xlsx, metadata_only=True)
    MFO.plot_scan_media_folders()


else:
    print(f'-- Unrecognized answer "{text_a1}". Please rerun and enter A or B.')




#[20] Complete
print(f'\nCompleted {os.path.basename(__file__)}. Close in 5 seconds.')
time.sleep(5)
