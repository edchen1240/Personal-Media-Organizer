"""
[PMO-06_all directory one level up.py]
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
from PersonalMediaOrganizer import M3_Image as M3I

if __name__ == '__main__':
    #[1] Ask folder location
    #path_img = r'D:\01_Floor\a_Ed\09_EECS\10_Python\05_Complete\2022-0603_Personal Media Organizer\MFS-02_Geo\IMG_1270.JPG'
    path_img, bsn_img = M1F.tkinter_select_file(dialog_title='Select a file')

    if not path_img:
        print('\nNo file selected. Exiting.')
        time.sleep(2)
    else:
        print(f'\n[path_img] {path_img}\n')
        url_gmap = M3I.extract_gps_from_image_and_open_google_map(path_img)
        print('\nCompleted. Close in 5 seconds.')
        time.sleep(5)







