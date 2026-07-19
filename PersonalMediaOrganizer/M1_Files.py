"""
[M1_Utilities]
Purpose: Check the device for the LMS system.
Author: Meng-Chi Ed Chen
Date: 2024-0613

Status: Complete.
"""

import os, sys, time, shutil, gc, tkinter, subprocess, re, openpyxl
from tkinter import filedialog
import pillow_heif

import numpy as np
from datetime import datetime
import pandas as pd
from PIL import UnidentifiedImageError, Image, ExifTags
from tabulate import tabulate
import exifread
import webbrowser
import imageio.v3 as iio


from PersonalMediaOrganizer import M3_Image as M3I



# ==============================
#[1] Direcotory and file - Start
# ==============================

def find_certain_ext_in_dir(dir_folder, ext):
    list_paths = [os.path.join(dir_folder, file) for file in os.listdir(dir_folder) if file.endswith(ext)]
    list_bsns = [file for file in os.listdir(dir_folder) if file.endswith(ext)]
    return list_paths, list_bsns





def find_list_exts_in_dir(  dir_folder, 
                            list_exts, 
                            list_kwd_exclude = ['processed', 'bat', 'exclude']):
    """
    Fing files with certain extensions in a directory, 
    excluding those with specified keywords.
    """
    #[1] Normalize extensions
    if list_exts is None:
        exts = None
    else:
        if isinstance(list_exts, str):
            list_exts = [list_exts]
        exts = [('.' + s.lstrip('.')).lower() for s in (x.strip() for x in list_exts) if s and s.strip()]
        if not exts:
            exts = None
    
    #[3] Filter files
    list_paths  = [f for f in os.listdir(dir_folder) if os.path.isfile(os.path.join(dir_folder, f))]
    list_bsns   = [f for f in list_paths
                    if not any(kwd in f.lower() for kwd in list_kwd_exclude)
                    and (exts is None or any(f.lower().endswith(ext) for ext in exts))]
    list_paths = [os.path.join(dir_folder, f) for f in list_bsns]
    cnt_files = len(list_paths)
    return list_paths, list_bsns, cnt_files






def get_working_dir_from_sysargv():
    dir_working, dir_bsn = None, None
    #[1] Retrieve the working directory from command-line arguments
    #print(f'sys.argv = {sys.argv}')
    
    if len(sys.argv) < 2:
        raise ValueError(f'\n-- No working directory provided from sys.argv:\n{sys.argv}\n-- Use the existing dir_img_folder in code.')
    elif 'ipykernel_launcher.py' in sys.argv[0]:
        raise ValueError('\n-- Detected ipynb environment. Please provide dir_working manually in the code.')
    else:
        raw = sys.argv[1]
        #[3] sanitize: trim whitespace and remove surrounding quotes (handles cases like ...SARD-03_launchers")
        if isinstance(raw, str):
            raw = raw.strip()
            if raw[0] in ['"', "'"]:
                raw = raw[1:]
            if raw[-1] in ['"', "'"]:
                raw = raw[:-1]
        dir_working = os.path.normpath(raw)
        timestamp = datetime.now().strftime("%Y-%m%d-%H%M%S")
        print(f'-- [{timestamp}] Working directory received: \n{dir_working}')
        dir_bsn = os.path.basename(dir_working)
        
    return dir_working, dir_bsn






def preview_files_and_folders_in_dir(dir_folder, preview_cnt=20):
    """
    Keep this preview function simple. Do not add other function like file_only or list_bsn.
    """
    print(f'\n[preview_files_and_folders_in_dir] {dir_folder}')
    try:
        #[1] Check if the directory exists
        if not os.path.isdir(dir_folder):
            raise FileNotFoundError(f"The directory '{dir_folder}' does not exist.")
        
        #[2] List all files and folders in the directory
        list_folder_and_files = os.listdir(dir_folder)
        
        #[3] Limit the number of entries to the first `first_cnt_files`
        limited_list = list_folder_and_files[:preview_cnt]
        
        #[4] Print each entry on a new line
        cnt = len(limited_list)
        for i, entry in enumerate(limited_list):
            print(f'-- [{i+1:03d}/{cnt:03d}] \t{entry}')
        
        return limited_list
    
    except Exception as e:
        print(f"Error: {e}")


def tkinter_select_directory(dialog_title='Select a directory'):
    
    #[1] Initiate and hide the main window.
    root = tkinter.Tk()
    root.withdraw()
    
    try:
        path_dir = tkinter.filedialog.askdirectory(title=dialog_title)
        if path_dir:
            #[2] Extract the base name of the selected directory.
            bsn_dir = os.path.basename(path_dir)
            #[3] Clean the path and append the trailing separator.
            path_dir = os.path.normpath(path_dir) + os.sep
            print('--path_dir:', path_dir)
            return path_dir, bsn_dir
        else:
            #[4] Exit the program if no directory is selected.
            print('--No directory selected. Exiting.')
            sys.exit()
    except Exception as e:
        print(f'--An error occurred: {e}')
        return None, None
    finally:
        #[5] Clean up and destroy the Tkinter window.
        root.destroy()
        


def filter_file_in_dir_with_keywords(dir_folder, list_kwd_yes_or_1=[], list_kwd_no_or_2=[], print_bsn = False):
    #print(f'\n[filter_file_in_dir_with_keywords] list_kwd_yes_or_1: {list_kwd_yes_or_1}. list_kwd_no_or_2: {list_kwd_no_or_2}')
    #[1] Check if directory exists
    if not os.path.isdir(dir_folder):
        raise FileNotFoundError(f"The directory '{dir_folder}' was not found.")
    
    #[2] Get list of files in the directory, no folders.
    list_bsn = [file for file in os.listdir(dir_folder) if os.path.isfile(os.path.join(dir_folder, file))]
    cnt_before = len(list_bsn)
    
    #[3] Filter names by keywords to select
    if list_kwd_yes_or_1:
        list_bsn = [file for file in list_bsn if any(keyword in file for keyword in list_kwd_yes_or_1)]
    
    #[4] Filter names by keywords to discard
    if list_kwd_no_or_2:
        list_bsn = [file for file in list_bsn if not any(keyword in file for keyword in list_kwd_no_or_2)]
        
    #[5] Generate file paths and orint
    list_paths = [os.path.join(dir_folder, file) for file in list_bsn]
    cnt_after = len(list_bsn)
    if print_bsn:
        print(f'\n--  Count (before, after) = {cnt_before}, {cnt_after}. list_bsn: \n{list_bsn}', end='\n\n')
    return list_paths, list_bsn




def filter_folders_in_dir_with_keywords(dir_folder, list_kwd_yes_or_1=[], list_kwd_no_or_2=[], print_bsn=False):
    print(f'\n[filter_folders_in_dir_with_keywords] dir_folder = {dir_folder}')
    
    #[1] Check if directory exists
    if not os.path.isdir(dir_folder):
        raise FileNotFoundError(f'The directory {dir_folder} was not found.')
    
    #[2] Get list of folders in the directory, no files.
    list_bsns = [folder for folder in os.listdir(dir_folder) if os.path.isdir(os.path.join(dir_folder, folder))]
    cnt_before = len(list_bsns)
    
    #[3] Filter folder names by keywords to select (if list_kwd_yes_or_1 is not empty list).
    if list_kwd_yes_or_1 != []:
        list_bsns = [folder for folder in list_bsns if any(keyword in folder for keyword in list_kwd_yes_or_1)]
    
    #[4] Filter folder names by keywords to discard (if list_kwd_no_or_2 is not empty list).
    if list_kwd_no_or_2 != []:
        list_bsns = [folder for folder in list_bsns if not any(keyword in folder for keyword in list_kwd_no_or_2)]
    
    #[5] Generate folder paths and print
    list_dirs = [os.path.join(dir_folder, folder) for folder in list_bsns]
    cnt_after = len(list_bsns)
    if print_bsn:
        print(f'\n--  Count (before, after) = {cnt_before}, {cnt_after}. list_bsns: \n{list_bsns}', end='\n\n')
    return list_dirs, list_bsns




"""
Try to avoid using program to delete files because it's irreversible. Just name the dump_folder_name='01_delete' and then delete it mannually later.
Don't add a variable of delete=False.
"""

def batch_file_relocate(dir_folder, list_kwd_yes_or_1=[], list_kwd_no_or_2=[], dump_folder_name='01_dump', print_bsn=False):
    print(f'\n[batch_file_relocate] list_kwd_yes_or_1:{list_kwd_yes_or_1}.  list_kwd_no_or_2:{list_kwd_no_or_2}. ')
    
    #[1] Filter files
    list_paths, list_bsn = filter_file_in_dir_with_keywords(dir_folder, list_kwd_yes_or_1, list_kwd_no_or_2, print_bsn)
    cnt = len(list_paths)
    if cnt == 0:
        print(f'There is nothing we need to move. File count = {cnt}.')
        return [], []
    
    #[2] Create a dump folder if it does not exist
    dir_dump = os.path.join(dir_folder, dump_folder_name)
    if not os.path.exists(dir_dump):
        os.mkdir(dir_dump)
        print("--Directory didn't exist. Just created one.")
    else:
        print("--Directory already exists. Skipping directory creation.")
    
    #[4] Iterate through file list to move files
    for iter_file in list_paths:
        file_name = os.path.basename(iter_file)
        destination_path = os.path.join(dir_dump, file_name)
        
        #[5] Move the file and handle potential naming conflicts
        try: 
            shutil.move(iter_file, destination_path)
        except shutil.Error:
            bsn_ext = os.path.splitext(file_name)
            suffix = 1
            new_file_name = f'{bsn_ext[0]}_dup{suffix}{bsn_ext[1]}'
            new_destination_path = os.path.join(dir_dump, new_file_name)
            
            while os.path.exists(new_destination_path):
                suffix += 1
                new_file_name = f'{bsn_ext[0]}_dup{suffix}{bsn_ext[1]}'
                new_destination_path = os.path.join(dir_dump, new_file_name)
            
            shutil.move(iter_file, new_destination_path)
    
    #[6] Final report
    if print_bsn:
        print(f'--  Finish moving {cnt} files. list_bsn: \n{list_bsn}\n\n')
    
    return list_paths, list_bsn



def move_all_files_in_the_subdirs_into_main_dir(dir_main, print_status=False):
    """
    Moves all files in the subdirectories into the main directory.

    Parameters:
    dir_main (str): The main directory path.
    print_status (bool): Whether to print status messages. Default is True.
    """
    print('\n[move_all_files_in_the_subdirs_into_main_dir]')
    #[1] Ensure the main directory ends with a slash
    dir_main = os.path.join(dir_main, '')

    if not os.path.isdir(dir_main):
        print(f'Provided path is not a directory: {dir_main}')
        return

    #[2] List all items in the main directory
    items_main_dir = os.listdir(dir_main)

    for i, item in enumerate(items_main_dir):
        sub_dir_path = os.path.join(dir_main, item)

        #[3] Check if the item is a directory
        if os.path.isdir(sub_dir_path):
            if print_status:
                print(f'[{i:04d}] \tProcessing folder: {item}')

            items_sub_dir = os.listdir(sub_dir_path)

            for sub_item in items_sub_dir:
                sub_item_full_path = os.path.join(sub_dir_path, sub_item)
                new_item_path = os.path.join(dir_main, sub_item)

                #[4] Move the file from the subdirectory to the main directory
                try:
                    os.rename(sub_item_full_path, new_item_path)
                    if print_status:
                        print(f'-- \tMoved: {sub_item} \tto {os.path.basename(dir_main)}')
                except FileExistsError:
                    if print_status:
                        print(f'-- File already exists: {new_item_path}. Skipping.')
                except FileNotFoundError:
                    if print_status:
                        print(f'-- File not found: {sub_item_full_path}. Skipping.')
                except Exception as e:
                    if print_status:
                        print(f'-- Error moving file {sub_item_full_path}: {e}')

    #[5] Delete empty folders
    print('\n[removing empty folders]')
    for item in items_main_dir:
        sub_dir_path = os.path.join(dir_main, item)

        if os.path.isdir(sub_dir_path):
            try:
                os.rmdir(sub_dir_path)
                if print_status:
                    print(f'-- Removed empty folder: {sub_dir_path}')
            except OSError:
                if print_status:
                    print(f'-- Folder not empty or cannot be removed: {sub_dir_path}')





def make_dir_if_not_exist(dir_to_make=None):
    #[1] If dir_to_make is not provided, make a dir at current directory with timestamp as folder name.
    if dir_to_make is None:
        dir_current = os.path.dirname(os.path.abspath(__file__))
        timestamp = datetime.now().strftime("%Y-%m%d-%H%M%S")
        dir_to_make = os.path.join(dir_current, f'{timestamp}_dir_name')
        
    #[2] Make dir.
    try:
        os.mkdir(dir_to_make)
        print("--Directory wasn't exists. Just made one.")
    except FileExistsError:
        print("--Directory already exists. Skipping directory creation.")




















# ==============================
#[2] File type statistic in dir and subdir - Start
# ==============================





def file_type_statistic_in_dir_and_subdir(path_dir, mb_limit, save_txt=True):
    print('\n[file_type_statistic_in_dir_and_subdir] Large file size limit =', mb_limit, 'MB')
    
    #[1] Initialize counters and lists
    total_files_found = 0
    total_folders_scanned = 0
    list_dir_bsn = []
    list_cnt_file_all = []
    list_cnt_file_docs = []
    list_cnt_file_musc = []
    list_cnt_file_imgs = []
    list_cnt_file_movs = []
    list_cnt_file_else = []
    list_cnt_oversize = []
    list_oversize_bsn = []
    
    #[2] Define the file extensions for each category
    ext_docs = ['.doc', '.docx', '.xlsx', '.txt']
    ext_musc = ['.mp3', '.wav', '.aac', '.flac']
    ext_imgs = ['.png', '.jpg', '.jpeg', '.gif', '.bmp']
    ext_movs = ['.mov', '.avi', '.mp4', '.mkv']
    
    #[3] Walk through the directory and its subdirectories
    for path_dir, list_subdir, list_bsn in os.walk(path_dir):
        total_folders_scanned += 1
        bsn_dir = os.path.basename(path_dir)
        
        #[4] Reset variables in the loop
        string_exceed_sub = ''
        sub_files_cnt = 0
        sub_files_docs = 0
        sub_files_musc = 0
        sub_files_imgs = 0
        sub_files_movs = 0
        sub_files_else = 0
        sub_files_oversize = 0
        
        #[5] Iterate through each file in the current directory
        for bsn_file in list_bsn:
            sub_files_cnt += 1
            path_file = os.path.join(path_dir, bsn_file)
            bsn_ext = os.path.splitext(bsn_file)[1].lower()
            
            file_size_mb = os.path.getsize(path_file) / 1048576
            
            #[6] Check if the file size exceeds the specified limit
            if file_size_mb > float(mb_limit):
                total_files_found += 1
                sub_files_oversize += 1
                if sub_files_oversize % 4 == 0:
                    string_exceed_sub += f'{bsn_file}\n'
                else:
                    string_exceed_sub += f'{bsn_file} '
            
            #[7] Count the number of files in each category based on the file extension
            if bsn_ext in ext_docs:
                sub_files_docs += 1
            elif bsn_ext in ext_musc:
                sub_files_musc += 1
            elif bsn_ext in ext_imgs:
                sub_files_imgs += 1
            elif bsn_ext in ext_movs:
                sub_files_movs += 1
            else:
                sub_files_else += 1
        
        #[8] Append data to lists
        list_dir_bsn.append(bsn_dir)
        list_cnt_file_all.append(sub_files_cnt)
        list_cnt_file_docs.append(sub_files_docs)
        list_cnt_file_musc.append(sub_files_musc)
        list_cnt_file_imgs.append(sub_files_imgs)
        list_cnt_file_movs.append(sub_files_movs)
        list_cnt_file_else.append(sub_files_else)
        list_cnt_oversize.append(sub_files_oversize)
        list_oversize_bsn.append(string_exceed_sub if string_exceed_sub else '')
    
    #[9] Create a DataFrame with the collected data
    df_report = pd.DataFrame({
        'dir_bsn': list_dir_bsn,
        'all': list_cnt_file_all,
        'docs': list_cnt_file_docs,
        'musc': list_cnt_file_musc,
        'imgs': list_cnt_file_imgs,
        'movs': list_cnt_file_movs,
        'else': list_cnt_file_else,
        'oversize': list_cnt_oversize,
        'oversize_bsn': list_oversize_bsn
    })
    sum_oversize = df_report['oversize'].sum()
    
    #[10] Optionally save a text report
    if save_txt:
        timestamp = datetime.now().strftime("%Y-%m-%d-%H%M")
        path_txt = os.path.join(path_dir, f'{timestamp}.txt')
        text = tabulate(df_report, headers='keys', tablefmt='orgtbl')
        with open(path_txt, 'w') as file:
            file.write(text)
    
    return df_report, sum_oversize







def single_folder_file_stat(dir_check):
    """
    Return file statistics within a folder.
    cnt_file: number of files.
    size_Mb: folder size in Mb.
    cnt_jpg: number of jpg or jpeg files.
    cnt_other_img: number of other image files.
    cnt_video: number of video files.
    """
    cnt_file = 0
    size_Mb = 0
    cnt_jpg = 0
    cnt_other_img = 0
    cnt_video = 0

    #[1] Define file extensions for categorization
    img_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp']
    video_extensions = ['.mov', '.avi', '.mp4', '.mkv']

    try:
        #[2] Iterate through files in the directory
        for root, dirs, files in os.walk(dir_check):
            for file in files:
                cnt_file += 1
                file_path = os.path.join(root, file)
                file_size = os.path.getsize(file_path) / (1024 * 1024)  # Convert size to MB
                size_Mb += file_size

                #[3] Get file extension
                ext = os.path.splitext(file)[1].lower()

                #[4] Categorize files
                if ext in ['.jpg', '.jpeg']:
                    cnt_jpg += 1
                elif ext in img_extensions:
                    cnt_other_img += 1
                elif ext in video_extensions:
                    cnt_video += 1

    except Exception as e:
        print(f"Error processing folder '{dir_check}': {e}")

    return cnt_file, round(size_Mb, 2), cnt_jpg, cnt_other_img, cnt_video


def batch_folder_file_stat(list_dirs):
    """
    Generate statistics for a list of directories.
    
    Returns a DataFrame with the following columns:
    - list_folder_bsn: Name of the folder.
    - list_cnt_file: Number of files in that folder.
    - list_size_Mb: Folder size in MB.
    - list_cnt_jpg: Number of jpg or jpeg files in that folder.
    - list_cnt_other_img: Number of other image files in that folder.
    - list_cnt_video: Number of video files in that folder.
    """
    print('\n[batch_folder_file_stat]')

    #[1] Initialize lists to store statistics for each folder
    list_folder_bsn = []
    list_cnt_file = []
    list_size_Mb = []
    list_cnt_jpg = []
    list_cnt_other_img = []
    list_cnt_video = []

    #[2] Iterate through each directory in the list
    for dir_path in list_dirs:
        try:
            #[3] Get folder statistics using the single_folder_file_stat function
            cnt_file, size_Mb, cnt_jpg, cnt_other_img, cnt_video = single_folder_file_stat(dir_path)

            #[4] Append the statistics to the respective lists
            list_folder_bsn.append(os.path.basename(dir_path))
            list_cnt_file.append(cnt_file)
            list_size_Mb.append(size_Mb)
            list_cnt_jpg.append(cnt_jpg)
            list_cnt_other_img.append(cnt_other_img)
            list_cnt_video.append(cnt_video)
        except Exception as e:
            print(f"Error processing folder '{dir_path}': {e}")

    #[5] Create a DataFrame with the collected statistics
    df_folders = pd.DataFrame({
        'list_folder_bsn': list_folder_bsn,
        'list_cnt_file': list_cnt_file,
        'list_size_Mb': list_size_Mb,
        'list_cnt_jpg': list_cnt_jpg,
        'list_cnt_other_img': list_cnt_other_img,
        'list_cnt_video': list_cnt_video
    })

    return df_folders










# ==============================
#[3] Windows specific functions (tkinter) - Start
# ==============================



def open_a_folder_on_windows(dir_folder):
    """Open the given folder in File Explorer on Windows."""
    normalized = os.path.normpath(dir_folder)
    if not os.path.isdir(normalized):
        print(f"The directory '{normalized}' does not exist.")
        return False

    try:
        os.startfile(normalized)
        return True
    except OSError as primary_exc:
        # Fall back to explorer without propagating Explorer's return code
        try:
            subprocess.Popen(['explorer', normalized])
            return True
        except Exception as fallback_exc:
            print(
                f"Error opening folder '{normalized}': {primary_exc}. "
                f"Fallback failed: {fallback_exc}"
            )
            return False




def add_date_to_file_name(path_file, date_str, date_format='%Y-%m%d', print_status=False, for_real=False):
    """
    Add a date string to the file name before the file extension.
    
    Parameters:
    - path_file: The full path of the file.
    - date_str: The date string to add.
    - date_format: The format of the date string (default is '%Y-%m-%d').
    - print_status: Whether to print the status of the operation.
    
    Returns:
    - new_path_file: The new file path with the date added to the name.
    """
    try:
        #[1] Extract the base name and extension from the file path
        bsn_file = os.path.basename(path_file)
        bsn_ext = os.path.splitext(bsn_file)
        
        #[2] Create the new file name
        new_bsn_file = f"{date_str}_{bsn_ext[0]}{bsn_ext[1]}"
        
        #[3] Construct the new file path
        new_path_file = os.path.join(os.path.dirname(path_file), new_bsn_file)
        
        #[4] Rename the file
        if for_real:
            os.rename(path_file, new_path_file)
            if print_status:
                print(f'File renamed from "{bsn_file}" to "{new_bsn_file}".')
        
        return new_path_file
    
    except Exception as e:
        print(f"Error adding date to file name: {e}")
        return None 



def tkinter_select_file(dialog_title='Select a file'):
    #[1] Create a window (or container) for the Tkinter GUI (Graphical User Interface) toolkit.
    root = tkinter.Tk()
    root.withdraw()  # Hide the main window since we don't need to see it.
    
    try:
        path_file = filedialog.askopenfilename(title=dialog_title)
        if path_file:
            #[2] Extract the base name of the selected file.
            bsn_file = os.path.basename(path_file)
            #[3] Clean the path.
            path_file = os.path.normpath(path_file)
            print('--path_file:', path_file)
            return path_file, bsn_file
        else:
            #[4] Exit the program if no file is selected.
            print('--No file selected. Exiting.')
            sys.exit()
    except Exception as e:
        print(f'--An error occurred: {e}')
        return None, None
    finally:
        #[5] Release resources.
        root.destroy()


def tkinter_select_directory(dialog_title='Select a directory'):
    
    #[1] Initiate and hide the main window.
    root = tkinter.Tk()
    root.withdraw()
    
    try:
        path_dir = tkinter.filedialog.askdirectory(title=dialog_title)
        if path_dir:
            #[2] Extract the base name of the selected directory.
            bsn_dir = os.path.basename(path_dir)
            #[3] Clean the path and append the trailing separator.
            path_dir = os.path.normpath(path_dir) + os.sep
            print('--path_dir:', path_dir)
            return path_dir, bsn_dir
        else:
            #[4] Exit the program if no directory is selected.
            print('--No directory selected. Exiting.')
            sys.exit()
    except Exception as e:
        print(f'--An error occurred: {e}')
        return None, None
    finally:
        #[5] Clean up and destroy the Tkinter window.
        root.destroy()







def tkinter_select_multiple_files(dialog_title='Select files', allow_close=False):
    """
    Necessary import statement:
    import os, sys, tkinter
    from tkinter import filedialog
    """
    #[1] Create a window (or container) for the Tkinter GUI (Graphical User Interface) toolkit.
    root = tkinter.Tk()
    root.withdraw()  # Hide the main window since we don't need to see it.
    
    try:
        # [2] Open a file dialog to select multiple files
        list_path_file = tkinter.filedialog.askopenfilenames(title=dialog_title)
        if list_path_file:
            # [3] Extract the base names of the selected files
            list_bsn_file = [os.path.basename(path_file) for path_file in list_path_file]
            # [4] Clean the paths
            list_path_file = [os.path.normpath(path_file) for path_file in list_path_file]
            print('--Selected files:', list_path_file)
            return list_path_file, list_bsn_file
        else:
            # [5] Allow no file selected
            if allow_close:
                return None, None
            # [6] Exit the program if no files are selected
            else:
                print('--No files selected. Exiting.')
                sys.exit()
    except Exception as e:
        print(f'--An error occurred: {e}')
        return None, None
    finally:
        # [7] Release resources
        root.destroy()






# ==============================
#[4] Reset files - Start
# ==============================


def copy_file_from_dir_to_dir(dir_src, dir_dst, list_ext = [], print_status=False):
    print(f'\n[copy_file_from_dir_to_dir] dir_src = {dir_src}. dir_dst = {dir_dst}. ')
    
    #[1] Check if source directory exists
    if not os.path.isdir(dir_src):
        raise FileNotFoundError(f'The source directory {dir_src} was not found.')
    
    #[2] Create destination directory if it does not exist
    if not os.path.exists(dir_dst):
        os.makedirs(dir_dst)
        print(f'-- Created destination directory: {dir_dst}')
    
    #[3] Get list of files in the source directory with specified extensions
    list_path_match = [ os.path.join(dir_src, file)
                            for file in os.listdir(dir_src)
                            if any(file.lower().endswith(ext) for ext in list_ext) ]
    cnt_match = len(list_path_match)
    
    #[4] Copy files to the destination directory
    for i, path_original in enumerate(list_path_match):
        bsn_file = os.path.basename(path_original)
        new_path_file = os.path.join(dir_dst, bsn_file)
        shutil.copy2(path_original, new_path_file)
        if print_status:
            print(f'[{i+1:03d}/{cnt_match}] Copied: {bsn_file}\n        to {dir_dst}')
    
    return list_path_match, cnt_match


def filter_files_by_extension(  dir_folder, 
                                list_ext            = [], 
                                include_or_exclude  = 'include', 
                                remove_file         = False):
    # print(f'\n[filter_files_by_extension]')
    
    #[1] Check if directory exists
    if not os.path.isdir(dir_folder):
        raise FileNotFoundError(f'The directory {dir_folder} was not found.')
    
    #[2] Get list of files in the directory, no folders.
    if include_or_exclude == 'include':
        list_path_match = [ os.path.join(dir_folder, file)
                                for file in os.listdir(dir_folder)
                                if any(file.lower().endswith(ext) for ext in list_ext) ]
        
    elif include_or_exclude == 'exclude':
        list_path_match = [ os.path.join(dir_folder, file)
                                for file in os.listdir(dir_folder)
                                if not any(file.lower().endswith(ext) for ext in list_ext) ]
    else:
        raise ValueError(f'Invalid value for include_or_exclude: {include_or_exclude}. Use "include" or "exclude".')
    cnt_match = len(list_path_match)
    
    #[3] Optionally remove files
    if remove_file:
        for i, path_original in enumerate(list_path_match):
            os.remove(path_original)
            print(f'[{i+1:03d}/{cnt_match}] \tRemoved: {os.path.basename(path_original)}')
    return list_path_match, cnt_match



def check_folder_and_reset_files(dir_parent, 
                                    kwd_test_run_folder = ['01_AAE', '02_HEIC', '03_Dup', '09_bkup'], 
                                    replace_with_bkup   = False,
                                    remove_date_tag     = False, 
                                    keep_only_HEIC      = False,
                                    exit_after_reset    = False,):
    """
    Used to automatically reset files after a test run, in order to prepare for a fresh run.
    Different process requires different reset approach.
    
    
    
    """
    
    print(f'\n[check_folders_with_keywords_exist] dir_parent = {dir_parent}')
    
    #[1] Count files and folders in the directory.
    cnt_file = len([file for file in os.listdir(dir_parent) if os.path.isfile(os.path.join(dir_parent, file))])
    cnt_folder = len([folder for folder in os.listdir(dir_parent) if os.path.isdir(os.path.join(dir_parent, folder))])
    print(f'-- There are {cnt_file} files and {cnt_folder} folders in the directory.')
    
    #[2] Filter folders with test run keywords
    list_dirs, list_bsn = filter_folders_in_dir_with_keywords(dir_parent, kwd_test_run_folder, [], False)
    cnt_test_folders = len(list_dirs)
    
    #[3] No test folders found - this is a fresh run
    if cnt_test_folders == 0:
        print('-- This is a fresh run. No folders found with the test run keywords.')
        return False
    bsn_bkup_folder = list_bsn[0]
    
    #[4] Test folders found - ask user if they want to reset
    print(f'-- Found {cnt_test_folders} folders with keywords: {list_bsn}.')
    user_response = question_and_if_yes_action(
        f'\nDo we need to reset files from {bsn_bkup_folder}? (yes to continue, no to skip this function.)\n'
        f'(Usually "no" during normal use rather than testing.)\n')
    
    if user_response in ['no', 'n', '', False]:
        print('-- User chose to skip the reset function.')
        return False
    
    #[5] User confirmed - move all files from subdirectories to main directory
    need_reset = True
    if replace_with_bkup is False:
        print('-- The previous run was a test run. Moving all files in the subdirectories into the main directory.')
        move_all_files_in_the_subdirs_into_main_dir(dir_parent, True)
        
    
    #[7] Settings
    allowed_media_ext = ['.avif', '.heic', '.webp', '.tif', '.tiff', '.bmp', 
                        '.jpeg', '.jpg', '.png', '.gif',
                        '.mp4', '.mov', '.avi', '.mkv', '.m4v']
    
    
    #[6] Optionally replace files with backup versions from the .bkup folder.
    if replace_with_bkup:
        print('-- Replacing files with backup versions from the .bkup folder.')
        #[1] Check if backup folder exists. Raise error if not.
        dir_bkup = os.path.join(dir_parent, bsn_bkup_folder)
        if not os.path.exists(dir_bkup):
            raise FileNotFoundError(f'Backup folder not found: {dir_bkup}. Please check.')
        
        #[2] Remove files with allowed_media_ext, keep folders.
        _, _ = filter_files_by_extension(dir_parent, list_ext=allowed_media_ext, include_or_exclude='include', remove_file=True)
            
        #[2] Copy files from backup folder to main directory.
        _, cnt_copied = copy_file_from_dir_to_dir(dir_bkup, dir_parent, list_ext=allowed_media_ext, print_status=True)
        print(f'-- Total files copied from backup: {cnt_copied}.')

    
    #[3] Optionally reset the datatime tag in the file name.
    if remove_date_tag:
        print('-- Resetting date time tag in file names.')
        #[1] Prepare file lists and create processed directory, ignoring .JPG

        list_path_original = [ os.path.join(dir_parent, file)
                                for file in os.listdir(dir_parent)
                                if any(file.lower().endswith(ext) for ext in allowed_media_ext) ]
        need_reset = True if len(list_path_original) > 0 else False
        
        #[3] The reset loop
        for i, path_original in enumerate(list_path_original):
            if re.match(r'^\d{4}-\d{4}_', os.path.basename(path_original)) or \
                re.match(r'^\d{4}-\d{2}_', os.path.basename(path_original)):
                
                #[4] Remove the date part from the file name.
                bsn_file = os.path.basename(path_original)
                bsn_new = re.sub(r'^\d{4}-\d{4}_', '', bsn_file)
                bsn_new = re.sub(r'^\d{4}-\d{2}_', '', bsn_new)
                new_path_file = os.path.join(dir_parent, bsn_new)
                os.rename(path_original, new_path_file)
                print(f'[{i+1:03d}/{len(list_path_original):03d}] \tRenamed: {bsn_file} \tto: {bsn_new}')
    
    
    #[4] If .HEIC and .jpg both exist, keep only HEIC.
    if keep_only_HEIC:
        print('-- Keeping only .HEIC files when both .HEIC and .jpg exist.')
        #[1] Prepare file lists
        list_bsn_heic = [ file for file in os.listdir(dir_parent) if file.lower().endswith('.heic') ]
        cnt_removed = 0
        
        #[2] The removal loop
        for bsn_heic in list_bsn_heic:
            bsn_jpg = f'{os.path.splitext(bsn_heic)[0]}.jpg'
            path_jpg = os.path.join(dir_parent, bsn_jpg)
            if os.path.exists(path_jpg):
                os.remove(path_jpg)
                cnt_removed += 1
                print(f'-- Removed: {bsn_jpg} since {bsn_heic} exists.')
        print(f'-- Total .jpg files removed: {cnt_removed}.')
        
    #[5] Exit if specified.
    if exit_after_reset and need_reset:
        sys.exit('-- Exiting after reset as per the flag.')
    print('-- All files have been moved to the main directory. Pause for 3 seconds.')
    time.sleep(3)
    
    
    return need_reset












# ==============================
#[5] Text - Start
# ==============================



def create_txt_and_save_text(path_txt, text, open_file=True):
    print('\n[create_txt_and_save_text]')
    
    #[1] Ensure the directory where the file will be saved exists.
    os.makedirs(os.path.dirname(path_txt), exist_ok=True)
    
    #[2] Open the file in write mode ('w'), which will create the file if it doesn't exist.
    with open(path_txt, 'w') as file:
        file.write(text)
        
    #[3] After saving, optionally open the txt file.
    if open_file:
        #[4] Check the platform and open the file accordingly.
        if os.name == 'nt':             # For Windows
            os.startfile(path_txt)
        elif os.name == 'posix':        # For MacOS
            subprocess.run(['open', path_txt])
        else:                           # For Linux (xdg-open should work for most environments)
            subprocess.run(['xdg-open', path_txt])
            



# ==============================
#[6] Array, Dataframe, Dictionary, and Excel - Start
# ==============================

def save_df_as_excel_overwrite(df, path_xlsx, sheet_name, index=False):
    print('\n[save_df_as_excel_overwrite]')
    
    #[1] Make dir if not exist.
    dir_excel = os.path.dirname(path_xlsx)
    if not os.path.exists(dir_excel):
        os.makedirs(dir_excel)

    #[2] Try saving, wait if file is open
    while True:
        try:
            if os.path.exists(path_xlsx):
                with pd.ExcelWriter(path_xlsx, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                    df.to_excel(writer, sheet_name=sheet_name, index=index)
            else:
                with pd.ExcelWriter(path_xlsx, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name=sheet_name, index=index)
            break  # success: break loop

        except PermissionError:
            text_warning = f'\n⚠️[Warning] Cannot write to "{path_xlsx}"!\n'\
                            f'Did you close the excel fiel? Please close the file and hit Enter to try again.'
            print(text_warning)
            input('-- Press Enter after closing the Excel file...')

    print(f'-- Dataframe saved to {path_xlsx} in sheet {sheet_name}', end='\n\n')






def read_excel_sheet_into_df(path_xlsx, sheet_name=None, print_header=False):
    #[1] Read the Excel file into a DataFrame
    if sheet_name is None:
        sheet_name = 0  # Assuming 0 is the index of the first sheet
    df = pd.read_excel(path_xlsx, sheet_name=sheet_name)
    
    #[2] Tabulate the head of the DataFrame
    text_header = f"\n[read_excel_into_df] DataFrame Head:\n--\n"\
                  f"{tabulate(df.head(), headers='keys', tablefmt='orgtbl')}\n--\n"
    if print_header:
        print(text_header)
    del text_header
    return df



def adjust_multiple_column_widths(path_xlsx, sheet_name, list_column_letters, list_column_widths):
    print('\n[adjust_multiple_column_widths]')
    #[1] Check if list_column_letters and list_column_widths have the same length
    if len(list_column_letters) != len(list_column_widths):
        raise TypeError('The length of list_column_letters and list_column_widths are different, please check.')
    workbook = openpyxl.load_workbook(path_xlsx)
    
    #[2] Check if sheet_name exist
    if sheet_name not in workbook.sheetnames:
        print(f"--Sheet '{sheet_name}' does not exist in the workbook.")
        return
    worksheet = workbook[sheet_name]
    
    #[3] Adjust column width
    for col_letter, col_width in zip(list_column_letters, list_column_widths):
        worksheet.column_dimensions[col_letter].width = col_width
        print(f"--Column '{col_letter}' in sheet '{sheet_name}' has been adjusted to width {col_width}.")
    workbook.save(path_xlsx)
    print("--All specified columns have been adjusted.", end='\n\n')



def save_dict_as_excel_overwrite(dict_input, path_xlsx, sheet_name='dict'):
    """
    Save a plain Python dictionary to Excel as a two-column key/value table.
    The resulting sheet will contain a header row and two columns:
    ['key', 'value'].
    This is expected to work with the function read_excel_with_two_columns_into_dict().
    
    Uses save_df_as_excel_overwrite so other sheets in the workbook are preserved.
    """
    print('\n[save_dict_as_excel_overwrite]')
    #[1] Validate that dict_input is a dictionary
    if not isinstance(dict_input, dict):
        raise TypeError(f'\n🚨[Error] The provided input is not a dictionary.')

    #[2] Convert the dictionary to a two-column DataFrame and save it.
    #    Prefix values that start with '=' so Excel does not treat them as formulas.
    list_items = []
    for k, v in dict_input.items():
        if isinstance(v, str) and v.startswith('='):
            v = "'" + v
        list_items.append((k, v))
    df = pd.DataFrame(list_items, columns=['key', 'value'])
    save_df_as_excel_overwrite(df, path_xlsx, sheet_name, index=False)
    

def read_excel_with_two_columns_into_dict(path_xlsx, sheet_name):
    """
    Read an Excel sheet that contains a two-column key/value table and return it as a dictionary.
    The sheet is expected to work with the function save_dict_as_excel_overwrite().
    """
    print('\n[read_excel_with_two_columns_into_dict]')
    #[1] Read the specified sheet into a DataFrame
    df = pd.read_excel(path_xlsx, sheet_name=sheet_name)
    
    #[2] Check if the DataFrame has at least two columns
    if df.shape[1] < 2:
        raise ValueError(f'\n🚨[Error] The sheet "{sheet_name}" must have at least two columns. It is now {df.shape} columns.')
    
    #[3] Create a dictionary from the first two columns
    dict_output = pd.Series(df.iloc[:, 1].values, index=df.iloc[:, 0]).to_dict()
    
    print(f'--Dictionary created from {path_xlsx} - {sheet_name}', end='\n\n')
    return dict_output














# ==============================
#[7] Interation - Start
# ==============================


def ask_for_input(question_message, readback=True, allow_empty=True):
    """
    Ed Chen's function, 2025-06-06.
    """
    print('\n[ask_for_input] ', end='')
    while True:
        str_find = input(question_message).strip()
        #[3] Check if str_find is not empty or if empty input is allowed
        if str_find or allow_empty:  
            if readback:
                print(f'-- User said: {str_find}')
            return str_find
        else:
            print('-- Please enter a non-empty value!')

def question_and_if_yes_action(yes_no_question, action_if_yes=None):
    """
    2025-0912-0958: Keep this function updated in F05_Interaction.py.
    """
    #[1] Asks a yes/no question, and if the answer is yes, executes the given action (function).
    answer = ask_for_input(yes_no_question, readback=True, allow_empty=False)
    if any(keyword in answer.lower() for keyword in ['yes', 'ye', 'y', 'ok', 'okey', 'sure', 'go', 'aff', 'affirmative']):
        print('-- User agreed to proceed.', answer)
        return action_if_yes() if action_if_yes is not None else True
    else:
        #sys.exit('-- User chose to exit.')
        return False








