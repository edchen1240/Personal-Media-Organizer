"""
[PMO-21_GPS info at file level.py]
Purpose: Get "date taken" of photos and videos.
Author: Meng-Chi Ed Chen
Date: 2022-06-11
Reference:
    1.https://thispointer.com/python-get-list-of-files-in-directory-sorted-by-date-and-time/
    2.

Status: Final complete version.
"""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PersonalMediaOrganizer import M1_Files as M1F
from PersonalMediaOrganizer import M3_Image as M3I
from PersonalMediaOrganizer import M4_Classes as M4C
from PersonalMediaOrganizer import M5_Statistics as M5S

if __name__ == '__main__':
    #[2] Input settings.
    dir_work =      r'D:\01_Floor\b_Memory\01_DailyPhotosVedios_2021-2030'
    dir_output =    r'D:\01_Floor\a_Ed\09_EECS\10_Python\05_Complete\2022-0603_Personal Media Organizer\01_tests\PMO-21_GPS Stat'
    date_start =    '2021-02-01'
    date_end =      '2021-03-31'


    #[3] Get GPS info and save to Excel.
    FLGPSE = M5S.FileLevelGPSInfoExport(dir_work        = dir_work,
                                        date_start      = date_start,
                                        date_end        = date_end,
                                        dir_output      = dir_output,
                                        city_name       = False
                                        )


    #[15] Complete.
    print('\nCompleted. Close in 5 seconds.')
    time.sleep(5)
