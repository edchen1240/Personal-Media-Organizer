"""
[M1_Utilities]
Purpose: Check the device for the LMS system.
Author: Meng-Chi Ed Chen
Date: 2024-0613

Status: Complete.
"""

import os, sys, time, shutil, gc, tkinter, ffmpeg
from tkinter import filedialog
import pillow_heif

import numpy as np
import re
from datetime import datetime, timezone
import pandas as pd
from PIL import UnidentifiedImageError, Image, ExifTags
from tabulate import tabulate
import exifread
import webbrowser
import imageio.v3 as iio

# Register HEIF opener globally
try:
    pillow_heif.register_heif_opener()
except Exception as e:
    print(f"Warning: Failed to register HEIF opener: {e}")




#[1] Media Datetime - Start


def _parse_video_clock(tag_value, assume_utc=False):
    """
    Read a QuickTime/ISO datetime tag as the clock time to stamp on the file.
    Apple creationdate is local wall time (2026-09-25T09:35:10-0400); keep that clock.
    creation_time is UTC (2026-09-25T13:35:10.000000Z); convert it to local time.
    """
    if not tag_value:
        return None
    match = re.match(
        r'(\d{4}-\d{2}-\d{2})[T ](\d{2}:\d{2}:\d{2})',
        str(tag_value).strip())
    if not match:
        return None
    clock = datetime.strptime(f'{match.group(1)} {match.group(2)}', '%Y-%m-%d %H:%M:%S')
    if not assume_utc:
        return clock
    return clock.replace(tzinfo=timezone.utc).astimezone().replace(tzinfo=None)


def retrieve_datetime_of_video(path_media, datetime_format):
    """
    Prefer the camera's recorded time over the filesystem modified time.
    iPhone MOV stores com.apple.quicktime.creationdate in local time.
    File mtime is often the copy/export time and is wrong for dating.
    """
    try:
        tags = (ffmpeg.probe(path_media).get('format') or {}).get('tags') or {}
    except Exception as e:
        print(f'Warning: video metadata probe failed for {os.path.basename(path_media)}: {e}')
        tags = {}

    recorded = _parse_video_clock(tags.get('com.apple.quicktime.creationdate'), assume_utc=False)
    if recorded is not None:
        return recorded.strftime(datetime_format), '[1] quicktime.creationdate(video)'

    recorded = _parse_video_clock(tags.get('creation_time'), assume_utc=True)
    if recorded is not None:
        return recorded.strftime(datetime_format), '[1] creation_time UTC to local(video)'

    media_datetime = datetime.fromtimestamp(os.path.getmtime(path_media)).strftime(datetime_format)
    return media_datetime, '[3] os.path.getmtime(video)'


# This retrieve_datetime_of_single_media_files function is a 
def retrieve_datetime_of_single_media_files(path_media, 
                                            datetime_format = '%Y-%m-%d, %H:%M:%S'):
    #[2] Get file extension
    bsn_ext = os.path.basename(path_media)
    bsn, ext = os.path.splitext(bsn_ext)
    ext = ext.upper()
    
    #[3] Check file type for image
    if ext in ['.JPG', '.JPEG', '.PNG', '.GIF', '.TIF']:
        try:
            media_datetime = datetime.strptime(Image.open(path_media)._getexif()[36867], 
                                                '%Y:%m:%d %H:%M:%S').strftime(datetime_format)
            method = '[1] get_date_taken(image)'
        except (KeyError, UnidentifiedImageError, TypeError, AttributeError):
            media_datetime = datetime.fromtimestamp(os.path.getmtime(path_media)).strftime(datetime_format)
            method = '[2] os.path.getmtime(image)'
    
    #[3.1] Check file type for HEIC
    elif ext == '.HEIC':
        try:
            # Try to get EXIF data from HEIC
            img = Image.open(path_media)
            if hasattr(img, '_getexif') and img._getexif():
                media_datetime = datetime.strptime(img._getexif()[36867], 
                                                    '%Y:%m:%d %H:%M:%S').strftime(datetime_format)
                method = '[1] get_date_taken(HEIC)'
            else:
                raise AttributeError("No EXIF data")
        except (KeyError, UnidentifiedImageError, TypeError, AttributeError):
            media_datetime = datetime.fromtimestamp(os.path.getmtime(path_media)).strftime(datetime_format)
            method = '[2] os.path.getmtime(HEIC)'
                
    #[4] Check file type for video. Use recorded time, not file mtime.
    elif ext in ['.MP4', '.MOV', '.M4V']:
        media_datetime, method = retrieve_datetime_of_video(path_media, datetime_format)
    
    #[5] Handle unknown file types
    else:
        media_datetime, method = None, None
        print(f'Unknown file type {bsn_ext}, usually AAE or other unsupported format.')
    return ext, media_datetime, method



def retrieve_datetime_from_list_of_media_files(list_path_media, 
                                               print_status=False, 
                                               datetime_format = '%Y-%m-%d, %H:%M:%S'):
    #[1] Initiate lists.
    cnt_total = len(list_path_media)
    list_media_datetime = []
    list_media_ext = []
    list_method = []
    
    for i, iter_path in enumerate(list_path_media):
        #[3] Get datetime from media file
        ext, media_datetime, method = retrieve_datetime_of_single_media_files(iter_path, datetime_format)
        
        #[6] Collect into lists.
        list_media_datetime.append(media_datetime)
        list_media_ext.append(ext)
        list_method.append(method)
        
        #[6] Optionally print status.
        if print_status:
            print(f'-- [{i:04d}/{cnt_total:04d}] \t{media_datetime}, \t{os.path.basename(iter_path)}, \t{method}.')
    
    return list_media_datetime, list_media_ext, list_method


def move_media_files_into_date_folders(list_path_media, list_media_datetime, print_status=False):
    print('\n[move_media_files_into_date_folders]')
    #[1] Initiate list
    list_result = []
    cnt_total = len(list_path_media)
    
    #[2] Iterate through files
    for i, iter_path in enumerate(list_path_media):
        #[4] Get directory
        iter_dir = os.path.dirname(iter_path)
        iter_bsn_ext = os.path.basename(iter_path)
        
        #[6] Create date folder if it does not exist
        iter_date = list_media_datetime[i].split(",", 1)[0]
        iter_dir_date = os.path.join(iter_dir, iter_date)
        if not os.path.exists(iter_dir_date):
            os.mkdir(iter_dir_date)
        
        #[7] Determine new file path
        new_iter_path = os.path.join(iter_dir_date, iter_bsn_ext)
        
        #[8] Move the file and handle potential conflicts
        if os.path.exists(new_iter_path):
            text_result = f'[{i:04d}/{cnt_total:04d}] \tFile already exists: {new_iter_path}. Skipping.'
        else:
            try:
                shutil.move(iter_path, new_iter_path)
                text_result = f'[{i:04d}/{cnt_total:04d}] \tMoved: {iter_bsn_ext} \tto: {iter_date}.'
            except FileNotFoundError:
                text_result = f'[{i:04d}/{cnt_total:04d}] \tFile not found: {iter_bsn_ext}.'
            except Exception as e:
                text_result = f'[{i:04d}/{cnt_total:04d}] \tError moving file {iter_bsn_ext}: {e}'
                
        #[10] Collect result and print.
        list_result.append(text_result)
        if print_status:
            print(f'{text_result}')
    return list_result

#[1] Media Datetime - End







#[3] Image conversion - Start

def replace_JPEG_to_JPG(dir):
    #[1] Identify all files with .jpeg extension
    list_path_JPEG = [os.path.join(dir, file) for file in os.listdir(dir) if file.lower().endswith('.jpeg')]
    list_path_JPG = []
    list_error = []
    print(f'\n[replace_JPEG_to_JPG] \n{list_path_JPEG}')
    
    #[2] Iterate through the JPEG files and rename them
    for path_JPEG in list_path_JPEG:
        try:
            path_JPG = f'{os.path.splitext(path_JPEG)[0]}.jpg'
            os.rename(path_JPEG, path_JPG)
            list_path_JPG.append(path_JPG)
        except Exception as e:
            text_e = f'Error renaming file {os.path.basename(path_JPEG)}: {str(e)}'
            list_error.append(text_e)
    
    return list_path_JPG, list_error


def make_dir_if_not_exist(dir_to_make=None):
    #[1] If dir_to_make is not provided, make a dir at current directory with timestamp as folder name.
    if dir_to_make is None:
        dir_current = os.path.dirname(os.path.abspath(__file__))
        timestamp = datetime.now().strftime("%Y-%m%d-%H%M%S")
        dir_to_make = os.path.join(dir_current, f'{timestamp}_dir_name')
        
    #[2] Make dir.
    try:
        os.mkdir(dir_to_make)
        print("-- Directory didn't exists. Just made one.")
    except FileExistsError:
        print("-- Directory already exists. Skipping directory creation.")


def remove_dir_if_empty(dir=None):
    #[14] Remove the processed_heic_dir if it's empty
    if dir is None:
        return 'No directory specified for removal.'
    if not os.listdir(dir):
        try:
            os.rmdir(dir)
            print(f'-- Removed empty folder: {dir}')
        except Exception as e:
            print(f'-- Error removing folder {dir}: {e}')


def delete_or_relocate_the_original_file(path_original, 
                                         dir_relocate, 
                                         delete_original=True, 
                                         print_status=False):
    bsn_ext_before_conv = os.path.basename(path_original)
    text_error = None
    
    #[10] Delete the original path_before_conv file if delete_or_remove is True.
    if delete_original:
        os.remove(path_original)
        if print_status:
            print(f'\t Original file removed: {bsn_ext_before_conv}')
            
    #[11] Otherwise, just move path_before_conv into dir_removed.
    else:
        try:
            shutil.move(path_original, dir_relocate)
            if print_status:
                print(f'\t Original file moved to processed directory: {bsn_ext_before_conv}')
        except FileNotFoundError:
            text_error = f'\tFile not found: {bsn_ext_before_conv}.'
        except Exception as e:
            text_error = f'\tError moving file {bsn_ext_before_conv}: {e}'

    return text_error




def convert_HEIC_to_JPG_and_keep_EXIF_info(dir, delete_or_remove=False, print_status=False, dump_dir_name='02_HEIC'):
    """
    2025-1116-1427: If you see error: 
        "Error opening file IMG_1007.HEIC with alternative method: 
        Invalid input: Unspecified: Too many auxiliary image references."
        Perform: pip install --upgrade pillow-heif Pillow
    
    """
    
    print('\n[convert_HEIC_to_JPG_and_keep_EXIF_info]')
    #[1] Extract HEIC files in the directory.
    list_path_HEIC = [os.path.join(dir, file) for file in os.listdir(dir) if file.lower().endswith('.heic')]
    cnt_HEIC = len(list_path_HEIC)
    list_path_JPG = []
    list_error = []
    
    #[2] Create a folder to store processed HEIC files.
    dir_processed_HEIC = os.path.join(dir, dump_dir_name)
    make_dir_if_not_exist(dir_processed_HEIC)
    list_no_exif = []

    #[3] Iterate through the HEIC files. HEIF opener is registered once at module import.
    for i, path_HEIC in enumerate(list_path_HEIC):
        #[4] Load the HEIC image.
        bsn_HEIC = os.path.basename(path_HEIC)
        if print_status:
            print(f'\n[{i:04d}/{cnt_HEIC:04d}] {bsn_HEIC}', end='')
        try:
            # Try opening with PIL first
            arrimg_HEIC = Image.open(path_HEIC)
        except UnidentifiedImageError:
            try:
                # If PIL fails, try direct pillow_heif method
                heif_file = pillow_heif.open_heif(path_HEIC)
                arrimg_HEIC = heif_file.to_pillow()
            except Exception as e:
                text_error = f'\n\t Error opening file {bsn_HEIC} with alternative method: {str(e)}.'
                list_error.append(text_error)
                if print_status:
                    print(text_error, end='')
                continue
        except Exception as e:
            try:
                # If standard PIL fails with other error, try pillow_heif method
                heif_file = pillow_heif.open_heif(path_HEIC)
                arrimg_HEIC = heif_file.to_pillow()
            except Exception as e2:
                text_error = f'\n\t Error opening file {bsn_HEIC}: PIL failed with {str(e)}, pillow_heif failed with {str(e2)}.'
                list_error.append(text_error)
                if print_status:
                    print(text_error, end='')
                continue
        
        #[5] Extract EXIF data and prepare path_JPG.
        exif_dict = arrimg_HEIC.info.get('exif')
        path_JPG = f'{os.path.splitext(path_HEIC)[0]}.jpg'
        
        #[6] Convert PIL Image to JPEG and save with EXIF data.
        if exif_dict:
            arrimg_HEIC.save(path_JPG, "JPEG", exif=exif_dict)
            if print_status:
                print(f'\t EXIF data found; copied to JPG.', end='')    # Most common result. We hope.
            list_path_JPG.append(path_JPG)

            #[7] Delete the original file or just move it (only when EXIF was kept).
            text_error = delete_or_relocate_the_original_file(path_HEIC, dir_processed_HEIC, delete_or_remove, print_status)
            if text_error is not None:
                list_error.append(text_error)

        #[8] No EXIF: save JPG, leave HEIC+JPG for manual decision, do not treat as success.
        else:
            arrimg_HEIC.save(path_JPG, "JPEG")
            list_no_exif.append(bsn_HEIC)
            text_error = (
                f'\n\t No EXIF for {bsn_HEIC}. '
                f'JPG saved; original HEIC left in place for manual decision.'
            )
            list_error.append(text_error)
            if print_status:
                print(text_error, end='')
            
        #[9] Explicitly close the image and free up memory.
        arrimg_HEIC.close()
        del arrimg_HEIC
        gc.collect()
    
    #[10] Summarize files that need manual review.
    if list_no_exif:
        print(f'\n-- {len(list_no_exif)} HEIC file(s) had no EXIF; left for manual decision:')
        for bsn in list_no_exif:
            print(f'   - {bsn}')

    #[11] Remove the processed_heic_dir if it's empty.
    text_error = remove_dir_if_empty(dir_processed_HEIC)
    if text_error:
        list_error.append(text_error)
    
    return list_path_JPG, list_error


def convert_WEBP_to_JPG_and_keep_EXIF_info(dir, delete_or_remove=False, print_status=False, dump_dir_name='03_WEBP (processed)'):
    print('\n[convert_WEBP_to_JPG_and_keep_EXIF_info]')
    #[1] Extract WEBP files in the directory.
    list_path_WEBP = [os.path.join(dir, file) for file in os.listdir(dir) if file.lower().endswith('.webp')]
    cnt_WEBP = len(list_path_WEBP)
    list_path_JPG = []
    list_error = []
    
    #[2] Create a folder to store processed WEBP files.
    dir_processed_WEBP = os.path.join(dir, dump_dir_name)
    make_dir_if_not_exist(dir_processed_WEBP)

    #[3] Iterate through the WEBP files.
    for i, path_WEBP in enumerate(list_path_WEBP):
        #[4] Load the WEBP image.
        bsn_WEBP = os.path.basename(path_WEBP)
        print(f'\t-- Processing {bsn_WEBP}')
        if print_status:
            print(f'\n[{i:04d}/{cnt_WEBP:04d}] \tProcessing: {bsn_WEBP}', end='')
        try:
            arrimg_WEBP = Image.open(path_WEBP)
        except UnidentifiedImageError as e:
            text_error = f'\n\t Error opening file {bsn_WEBP}: {str(e)}.'
            list_error.append(text_error)
            if print_status:
                print(text_error, end='')
            continue
        
        #[5] Extract EXIF data and prepare path_JPG.
        exif_dict = arrimg_WEBP.info.get('exif')
        path_JPG = f'{os.path.splitext(path_WEBP)[0]}.jpg'
        
        #[6] Convert PIL Image to JPEG and save with EXIF data.
        if exif_dict:
            arrimg_WEBP.save(path_JPG, "JPEG", exif=exif_dict)
            if print_status:
                print(f'\t EXIF data has been found and copied to JPG.', end='')
            list_path_JPG.append(path_JPG)

        #[7] Report if no EXIF data.
        else:
            arrimg_WEBP.save(path_JPG, "JPEG")
            text_error = f'\n\t No EXIF data has been found for \t{bsn_WEBP}.'
            list_error.append(text_error)
            if print_status:
                print(text_error, end='')
        
        #[8] Delete the original file or just move it.
        text_error = delete_or_relocate_the_original_file(path_WEBP, dir_processed_WEBP, delete_or_remove, print_status)
        if text_error is not None:
            list_error.append(text_error)
            
        #[9] Explicitly close the image and free up memory.
        arrimg_WEBP.close()
        del arrimg_WEBP
        gc.collect()
    
    #[10] Remove the processed_webp_dir if it's empty.
    text_error = remove_dir_if_empty(dir_processed_WEBP)
    if text_error:
        list_error.append(text_error)
    
    return list_path_JPG, list_error

def convert_AVIF_to_JPG_and_keep_EXIF_info(dir, delete_or_remove=False, print_status=False, dump_dir_name='04_AVIF (processed)'):
    print('\n[convert_AVIF_to_JPG_and_keep_EXIF_info]')
    #[1] Extract AVIF files in the directory.
    list_path_AVIF = [os.path.join(dir, file) for file in os.listdir(dir) if file.lower().endswith('.avif')]
    cnt_AVIF = len(list_path_AVIF)
    list_path_JPG = []
    list_error = []
    
    #[2] Create a folder to store processed AVIF files.
    dir_processed_AVIF = os.path.join(dir, dump_dir_name)
    make_dir_if_not_exist(dir_processed_AVIF)

    #[3] Iterate through the AVIF files.
    for i, path_AVIF in enumerate(list_path_AVIF):
        #[4] Load the AVIF image.
        bsn_AVIF = os.path.basename(path_AVIF)
        if print_status:
            print(f'\n[{i:04d}/{cnt_AVIF:04d}] \tProcessing: {bsn_AVIF}', end='')
        try:
            arrimg_AVIF = iio.imread(path_AVIF)
            pil_image = Image.fromarray(arrimg_AVIF)
        except Exception as e:
            text_error = f'\n\t Error opening file {bsn_AVIF}: {str(e)}.'
            list_error.append(text_error)
            if print_status:
                print(text_error, end='')
            continue
        
        #[5] Extract EXIF data and prepare path_JPG.
        exif_dict = pil_image.info.get('exif')
        path_JPG = f'{os.path.splitext(path_AVIF)[0]}.jpg'
        
        #[6] Convert PIL Image to JPEG and save with EXIF data.
        try:
            if pil_image.mode == 'RGBA':
                pil_image = pil_image.convert('RGB')
            if exif_dict:
                pil_image.save(path_JPG, "JPEG", exif=exif_dict)
                if print_status:
                    print(f'\t EXIF data has been found and copied to JPG.', end='')
            else:
                pil_image.save(path_JPG, "JPEG")
                text_error = f'\n\t No EXIF data has been found for \t{bsn_AVIF}.'
                list_error.append(text_error)
                if print_status:
                    print(text_error, end='')
            list_path_JPG.append(path_JPG)
                
            #[7] Delete the original file or just move it.
            text_error = delete_or_relocate_the_original_file(path_AVIF, dir_processed_AVIF, delete_or_remove, print_status)
            if text_error is not None:
                list_error.append(text_error)
            
        except Exception as e:
            text_error = f'\t Error saving JPG file {path_JPG}: {str(e)}.'
            list_error.append(text_error)
            if print_status:
                print(text_error, end='')
        
        #[8] Explicitly close the image and free up memory.
        pil_image.close()
        del pil_image
        gc.collect()
    
    #[9] Remove the processed_avif_dir if it's empty.
    text_error = remove_dir_if_empty(dir_processed_AVIF)
    if text_error:
        list_error.append(text_error)
    
    return list_path_JPG, list_error


def convert_TIFF_to_JPG_and_keep_EXIF_info(dir, delete_or_remove=False, print_status=False, dump_dir_name='05_TIFF (processed)'):
    print('\n[convert_TIF_to_JPG_and_keep_EXIF_info]')
    #[1] Extract TIF files in the directory.
    list_path_TIF = [os.path.join(dir, file) for file in os.listdir(dir) if file.lower().endswith('.tif') or file.lower().endswith('.tiff')]
    cnt_TIF = len(list_path_TIF)
    list_path_JPG = []
    list_error = []
    
    #[2] Create a folder to store processed TIF files.
    dir_processed_TIF = os.path.join(dir, dump_dir_name)
    make_dir_if_not_exist(dir_processed_TIF)

    #[3] Iterate through the TIF files.
    for i, path_TIF in enumerate(list_path_TIF):
        #[4] Load the TIF image.
        bsn_TIF = os.path.basename(path_TIF)
        if print_status:
            print(f'\n[{i:04d}/{cnt_TIF:04d}] \tProcessing: {bsn_TIF}', end='')
        try:
            arrimg_TIF = Image.open(path_TIF)
        except UnidentifiedImageError as e:
            text_error = f'\n\t Error opening file {bsn_TIF}: {str(e)}.'
            list_error.append(text_error)
            if print_status:
                print(text_error, end='')
            continue
        
        #[5] Extract EXIF data and prepare path_JPG.
        exif_dict = arrimg_TIF.info.get('exif')
        path_JPG = f'{os.path.splitext(path_TIF)[0]}.jpg'
        
        #[6] Convert the image to "RGB" mode if it's in "P" mode.
        if arrimg_TIF.mode == 'P':
            arrimg_TIF = arrimg_TIF.convert('RGB')

        #[7] Convert PIL Image to JPEG and save with EXIF data.
        if exif_dict:
            arrimg_TIF.save(path_JPG, "JPEG", exif=exif_dict)
            if print_status:
                print(f'\t EXIF data has been found and copied to JPG.', end='')
            list_path_JPG.append(path_JPG)

        #[8] Report if no EXIF data.
        else:
            arrimg_TIF.save(path_JPG, "JPEG")
            text_error = f'\n\t No EXIF data has been found for \t{bsn_TIF}.'
            list_error.append(text_error)
            if print_status:
                print(text_error, end='')
        
        #[9] Delete the original file or just move it.
        text_error = delete_or_relocate_the_original_file(path_TIF, dir_processed_TIF, delete_or_remove, print_status)
        if text_error is not None:
            list_error.append(text_error)
            
        #[10] Explicitly close the image and free up memory.
        arrimg_TIF.close()
        del arrimg_TIF
        gc.collect()
    
    #[11] Remove the processed_tif_dir if it's empty.
    text_error = remove_dir_if_empty(dir_processed_TIF)
    if text_error:
        list_error.append(text_error)
    
    return list_path_JPG, list_error







def convert_image_to_jpg_ignore_PNG(dir_cvt, 
                                    delete_original=False, 
                                    print_status=True, 
                                    dump_dir_name='02_Originals'):
    print(f'\n[convert_image_to_jpg_ignore_PNG]')
    allowed_image_ext = ['.AVIF', '.HEIC', '.WEBP', '.TIF', '.TIFF', '.BMP', '.JPEG', 'GIF']
     
    #[1] Prepare file lists and create processed directory
    list_path_original = [
    os.path.join(dir_cvt, file)
    for file in os.listdir(dir_cvt)
    if any(file.upper().endswith(ext) for ext in allowed_image_ext)]
        
    #[3] Prepare file lists and create processed directory
    cnt_original = len(list_path_original)
    list_path_JPG = []
    list_error = []
    
    dir_relocate = os.path.join(dir_cvt, dump_dir_name)
    make_dir_if_not_exist(dir_relocate)

    #[5] Process each image file
    for i, path_original in enumerate(list_path_original):
        bsn_ext = os.path.basename(path_original)
        bsn, ext = os.path.splitext(bsn_ext)
        ext = ext.upper()
        if print_status:
            print(f'\n[{i:04d}/{cnt_original:04d}] \tProcessing: {bsn_ext}', end='')
        
        try:
            #[7] Open image based on file type
            if ext == '.AVIF':
                arrimg_original = iio.imread(path_original)
                pil_image = Image.fromarray(arrimg_original)
            elif ext == '.HEIC':
                print(f'\t-- Processing HEIC file: {bsn_ext}')
                try:
                    pillow_heif.register_heif_opener()
                    pil_image = Image.open(path_original)
                except Exception as heic_error:
                    print(f'\t-- HEIC processing failed, trying alternative method: {heic_error}')
                    try:
                        # Try to read as raw data and convert
                        heif_file = pillow_heif.open_heif(path_original)
                        pil_image = heif_file.to_pillow()
                    except Exception as heic_error2:
                        print(f'\t-- Alternative HEIC method also failed: {heic_error2}')
                        # Skip this file and continue
                        text_error = f'\n\t Error processing HEIC file {bsn_ext}: Both methods failed.'
                        list_error.append(text_error)
                        continue
            elif ext in ['.WEBP', '.TIF', '.TIFF', '.BMP', '.JPEG', '.GIF']:
                pil_image = Image.open(path_original)
            else:
                raise ValueError(f'File {bsn_ext} has unsupported ext ({ext}).')
            
            #[4] Prepare EXIF data and JPG path
            exif_dict = pil_image.info.get('exif')
            path_JPG = f'{os.path.splitext(path_original)[0]}.jpg'
            
            #[5] Convert image mode if necessary
            if pil_image.mode in ['P', 'RGBA']:
                background = Image.new('RGB', pil_image.size, (255, 255, 255))  # White background
                pil_image = Image.alpha_composite(background.convert('RGBA'), pil_image.convert('RGBA')).convert('RGB')

            #[6] Save image as JPG with or without EXIF data
            if exif_dict:
                pil_image.save(path_JPG, "JPEG", exif=exif_dict)
                if print_status:
                    print(f'\t EXIF data has been found and copied to JPG.', end='')
                list_path_JPG.append(path_JPG)
            else:
                pil_image.save(path_JPG, "JPEG")
                text_error = f'\n\t No EXIF data has been found for \t{bsn_ext}.'
                list_error.append(text_error)
                if print_status:
                    print(text_error, end='')
            
            #[7] Handle original file (delete or move)
            text_error = delete_or_relocate_the_original_file(path_original, 
                                                              dir_relocate, 
                                                              delete_original, 
                                                              print_status)
            if text_error is not None:
                list_error.append(text_error)
                
        except Exception as e:
            text_error = f'\n\t Error processing file {bsn_ext}: {str(e)}.'
            list_error.append(text_error)
            if print_status:
                print(text_error, end='')
        
        finally:
            #[8] Clean up resources
            if 'pil_image' in locals():
                pil_image.close()
                del pil_image
            gc.collect()
    
    #[9] Remove relocate directory if empty
    text_error = remove_dir_if_empty(dir_relocate)
    if text_error:
        list_error.append(text_error)
    
    return list_path_JPG, list_error









def convert_image_to_PNG_ignore_JPG(dir_cvt, 
                                    delete_original=False, 
                                    print_status=True, 
                                    dump_dir_name='02_Originals'):
    print(f'\n[convert_image_to_PNG_ignore_JPG]')
    allowed_image_ext = ['.avif', '.heic', '.webp', '.tif', '.tiff', '.bmp', '.jpeg', '.svg']
     
    #[1] Prepare file lists and create processed directory, ignoring .JPG
    list_path_original = [
        os.path.join(dir_cvt, file)
        for file in os.listdir(dir_cvt)
        if any(file.lower().endswith(ext) for ext in allowed_image_ext) and not file.lower().endswith('.jpg')
    ]
        
    #[3] Prepare file lists and create processed directory
    cnt_original = len(list_path_original)
    list_path_PNG = []
    list_error = []
    
    dir_relocate = os.path.join(dir_cvt, dump_dir_name)
    make_dir_if_not_exist(dir_relocate)

    #[5] Process each image file
    for i, path_original in enumerate(list_path_original):
        bsn_ext = os.path.basename(path_original)
        bsn, ext = os.path.splitext(bsn_ext)
        ext = ext.lower()
        if print_status:
            print(f'\n[{i:04d}/{cnt_original:04d}] \tProcessing: {bsn_ext}', end='')
        
        try:
            #[7] Open image based on file type
            if ext == '.avif':
                arrimg_original = iio.imread(path_original)
                pil_image = Image.fromarray(arrimg_original)
            elif ext == '.heic':
                try:
                    pillow_heif.register_heif_opener()
                    pil_image = Image.open(path_original)
                except Exception as heic_error:
                    print(f'\t-- HEIC processing failed, trying alternative method: {heic_error}')
                    try:
                        # Try to read as raw data and convert
                        heif_file = pillow_heif.open_heif(path_original)
                        pil_image = heif_file.to_pillow()
                    except Exception as heic_error2:
                        print(f'\t-- Alternative HEIC method also failed: {heic_error2}')
                        # Skip this file and continue
                        text_error = f'\n\t Error processing HEIC file {bsn_ext}: Both methods failed.'
                        list_error.append(text_error)
                        continue
        
            elif ext == '.svg':
                import io, cairosvg
                #[1] Set output size for SVG conversion
                mtp_size = 2
                svg_width, svg_height = get_svg_size(path_original)
                png_bytes = cairosvg.svg2png(
                    url             = path_original,
                    output_width    = svg_width*mtp_size,
                    output_height   = svg_height*mtp_size)
                pil_image = Image.open(io.BytesIO(png_bytes)).convert('RGBA')
                #[2] Crop any fully transparent or black borders
                bg = Image.new('RGBA', pil_image.size, (0, 0, 0, 0))
                diff = Image.alpha_composite(bg, pil_image)
                bbox = diff.getbbox()
                if bbox:
                    pil_image = pil_image.crop(bbox)
                pil_image = pil_image.convert('RGB')  # Convert to RGB for PNG saving
                exif_dict = None  # SVGs don't have EXIF       
        
            elif ext in ['.webp', '.tif', '.tiff', '.bmp', '.jpeg']:
                pil_image = Image.open(path_original)
                if ext == '.jpeg':
                    # Convert .JPEG to .JPG first
                    path_JPG = f'{os.path.splitext(path_original)[0]}.jpg'
                    pil_image.save(path_JPG, "JPEG")
                    path_original = path_JPG
                    print(f'\t Converted {bsn_ext} to {os.path.basename(path_JPG)}.', end='')
            
            else:
                raise ValueError(f'File {bsn_ext} has unsupported ext ({ext}).')
            
            #[4] Prepare EXIF data and PNG path
            exif_dict = pil_image.info.get('exif')
            path_PNG = f'{os.path.splitext(path_original)[0]}.png'
            
            #[5] Convert image mode if necessary
            if pil_image.mode in ['P', 'RGBA']:
                pil_image = pil_image.convert('RGB')
            
            #[6] Save image as PNG with or without EXIF data
            if exif_dict:
                pil_image.save(path_PNG, "PNG", exif=exif_dict)
                if print_status:
                    print(f'\t EXIF data has been found and copied to PNG.', end='')
                list_path_PNG.append(path_PNG)
            else:
                pil_image.save(path_PNG, "PNG")
                text_error = f'\n\t No EXIF data has been found for \t{bsn_ext}.'
                list_error.append(text_error)
                if print_status:
                    print(text_error, end='')
            
            #[7] Handle original file (delete or move)
            text_error = delete_or_relocate_the_original_file(path_original, 
                                                              dir_relocate, 
                                                              delete_original, 
                                                              print_status)
            if text_error is not None:
                list_error.append(text_error)
                
        except Exception as e:
            text_error = f'\n\t Error processing file {bsn_ext}: {str(e)}.'
            list_error.append(text_error)
            if print_status:
                print(text_error, end='')
        
        finally:
            #[8] Clean up resources
            if 'pil_image' in locals():
                pil_image.close()
                del pil_image
            gc.collect()
    
    #[9] Remove relocate directory if empty
    text_error = remove_dir_if_empty(dir_relocate)
    if text_error:
        list_error.append(text_error)
    
    return list_path_PNG, list_error













def get_svg_size(svg_path):
    import xml.etree.ElementTree as ET

    tree = ET.parse(svg_path)
    root = tree.getroot()
    width = root.attrib.get('width')
    height = root.attrib.get('height')
    viewBox = root.attrib.get('viewBox')
    #[1] Try to parse width/height as float (strip units if present)
    def parse_dim(val):
        if val is None:
            return None
        for unit in ['px', 'pt', 'cm', 'mm', 'in']:
            val = val.replace(unit, '')
        try:
            return float(val)
        except:
            return None
    w = parse_dim(width)
    h = parse_dim(height)
    #[2] If width/height not found, try viewBox
    if w is None or h is None:
        if viewBox:
            parts = viewBox.strip().split()
            if len(parts) == 4:
                w = float(parts[2])
                h = float(parts[3])
    #[3] If still not found, print warning and set default sizes.
    if w is None or h is None:
        print(f'-- Warning: Could not determine SVG size for {svg_path}. Using default 1024x1024.')
        w, h = 1024, 1024
    return w, h










def convert_BMP_to_PNG_and_keep_EXIF_info(dir, delete_or_remove=False, print_status=False, dump_dir_name='06_BMP (processed)'):
    return None



#[3] Image conversion - End




#[4] Image - Start



def all_elements_same(list_dup_size):
    if len(list_dup_size) == 0:
        return True  # An empty list is considered to have all elements the same
    first_element = list_dup_size[0]
    return all(element == first_element for element in list_dup_size)


def move_duplicate_files_in_dir(dir, 
                                list_dup_split = [' (', ' - Copy'],
                                dup_folder='03_Dup'):
    """
    This function collect files with names containing list_dup_split that are possibly duplicates.
    Check for file names such as: IMG_0823.JPG, IMG_0823 (2).JPG, IMG_0823 (3).JPG.
    Not accepting HEIC file since they would be smaller in size and not comparable.
    It also use datetime to check if its duplicates.
    """
    #[1] Find potential duplicates.
    list_ext_exclude = ['.bat']
    list_potential_dup_main_name = []
    dir_dump = None
    for iter_bsn_ext in os.listdir(dir):
        #[3] Skip excluded extensions.
        if any(iter_bsn_ext.lower().endswith(ext) for ext in list_ext_exclude):
            continue
        
        #[4] Print unwanted files.
        iter_path = os.path.join(dir, iter_bsn_ext)
        bsn, ext = os.path.splitext(iter_bsn_ext)
        ext = ext.upper()
        if ext in ['.AAE', '.HEIC']:
            raise ValueError(f'Please remove AAE or HEIC files.')
        
        #[5] Check if it's a file and contains ' (' in the basename.
        if os.path.isfile(iter_path):
            for iter_dup_split in list_dup_split:
                if iter_dup_split in iter_bsn_ext:
                    main_name = iter_bsn_ext.split(iter_dup_split)[0]
                    list_potential_dup_main_name.append(main_name)


    #[6] Remove duplicate elements in the list.
    list_potential_dup_main_name = list(set(list_potential_dup_main_name))
    print(f'\n-- list_potential_dup_main_name: {list_potential_dup_main_name}')
        
    #[8] Iterate through potential duplicate names.
    list_path_main_name = []
    for iter_dup in list_potential_dup_main_name:
        list_dup_path = []
        list_dup_size = []
        list_dup_date = []
        
        #[10] Exam all the files again for set of potential duplicates.
        for iter_bsn_ext in os.listdir(dir):
            if iter_dup in iter_bsn_ext:
                #[12] Record name
                iter_dup_path = os.path.join(dir, iter_bsn_ext)
                list_dup_path.append(iter_dup_path)
                
                #[13] Collect size
                try:
                    size = os.path.getsize(iter_dup_path)
                except OSError as e:
                    print(f'Error getting size for file {iter_dup}: {e}') 
                list_dup_size.append(size)
                
                #[14] Collect date created.
                ext, media_datetime, method = retrieve_datetime_of_single_media_files(iter_dup_path)
                list_dup_date.append(media_datetime)
                
        #[16] Check if all the sizes and datetime are the same
        if len(list_dup_path) >= 1:
            #[19] Create folder to store duplicate files.
            dir_dump = os.path.join(dir, dup_folder)
            if not os.path.exists(dir_dump):
                os.mkdir(dir_dump)
            
            #[20] Move duplicate files (except the first one) inside dir_dump.
            print(f'\n[{iter_dup}]')
            print(f'-- list_dup_size: {list_dup_size}')
            print(f'-- list_dup_date: {list_dup_date}')
            if all_elements_same(list_dup_size) or all_elements_same(list_dup_date):
                
                #[22] Remove the shortest path, which might be the main one.
                path_main_name = min(list_dup_path, key=len)
                list_dup_path.remove(path_main_name)
                list_path_main_name.append(path_main_name)
                
                #[25] Move files.
                for i, iter_dup_path_dups in enumerate(list_dup_path):
                    new_iter_path = os.path.join(dir_dump, os.path.basename(iter_dup_path_dups))
                    try:
                        shutil.move(iter_dup_path_dups, new_iter_path)
                        text_result = f'[{i:04d}] \tMoved: {iter_bsn_ext} \tto: {dup_folder}.'
                    except FileNotFoundError:
                        text_result = f'[{i:04d}] \tFile not found: {iter_bsn_ext}.'
                    except Exception as e:
                        text_result = f'[{i:04d}] \tError moving file {iter_bsn_ext}: {e}'
                    print(text_result)
                else:
                    continue
    
    #[30] Remove dir_dump if it's empty.
    remove_dir_if_empty(dir_dump)
                
    return list_path_main_name




def convert_to_degrees(value):
    #[2.1] Helper function to convert GPS coordinates to decimal degrees.
    d = float(value.values[0].num) / float(value.values[0].den)
    m = float(value.values[1].num) / float(value.values[1].den)
    s = float(value.values[2].num) / float(value.values[2].den)
    return d + (m / 60.0) + (s / 3600.0)


def extract_latitude_and_longitude_from_path_img(path_img, city_name = True):
    #[1] Extract GPS info from EXIF of the image.
    bsn_img = os.path.basename(path_img)
    lat_deg, lon_deg = None, None
    str_city = None
    
    #[2] Use exifread to read EXIF data and extract GPS info.
    with open(path_img, 'rb') as file_img:
        tags = exifread.process_file(file_img)
        lat_ref = tags.get('GPS GPSLatitudeRef')
        lat = tags.get('GPS GPSLatitude')
        lon_ref = tags.get('GPS GPSLongitudeRef')
        lon = tags.get('GPS GPSLongitude')

        #[2] Convert latitude and longitude to decimal degrees.
        if lat and lon:
            lat_deg = convert_to_degrees(lat)
            if lat_ref.values != 'N':
                lat_deg = -lat_deg
            lon_deg = convert_to_degrees(lon)
            if lon_ref.values != 'E':
                lon_deg = -lon_deg
        
        #[5] Handle case where GPS info is not found.
        else:
            print(f'No GPS information found in the image: {bsn_img}')

    #[6] Reverse geocode to get city name.
    if lat_deg is not None and lon_deg is not None and city_name:
        import reverse_geocoder as rg
        result = rg.search((lat_deg, lon_deg), verbose=False)
        city  = result[0]['name']
        state = result[0]['admin1']
        str_city = f'{city}, {state}'

    return lat_deg, lon_deg, str_city








def extract_gps_from_image_and_open_google_map(path_img, print_status=True):
    #[1] Extract latitude and longitude using the helper function.
    lat_deg, lon_deg, str_city = extract_latitude_and_longitude_from_path_img(path_img)

    #[2] Open Google Maps if GPS coordinates are valid.
    if lat_deg is not None and lon_deg is not None:
        
        #[3] Print status.
        if print_status:
            print(f'-- Latitude: {lat_deg}, Longitude: {lon_deg}, City: {str_city}')
        
        url_gmap = f"https://www.google.com/maps/search/?api=1&query={lat_deg},{lon_deg}"
        
        #[5] Check if a web browser is available.
        if webbrowser.get():
            webbrowser.open_new_tab(url_gmap)
        else:
            print("No web browser found. Please open the following URL manually:")
            print(url_gmap)
        
        return url_gmap
    else:
        print("GPS coordinates could not be extracted.")
        return None



    

def rotate_image_files_upright(dir):
    print('\n[rotate_image_files_upright]')
    list_path_rotated = []
    
    #[1] Get all files as list in the directory.
    for iter_bsn_ext in os.listdir(dir):
        iter_path = os.path.join(dir, iter_bsn_ext)
        
        #[4] Select only image files.
        bsn, ext = os.path.splitext(iter_bsn_ext)
        ext = ext.upper()
        if ext in ['.JPG', '.JPEG', '.PNG', '.GIF']:
            try:
                with Image.open(iter_path) as img:
                    #[8] Find the EXIF orientation tag to get the rotation information.
                    for orientation in ExifTags.TAGS.keys():
                        if ExifTags.TAGS[orientation] == 'Orientation':
                            break

                    exif = img._getexif()
                    if exif is not None:
                        orientation = exif.get(orientation)
                        
                        if orientation == 3:
                            img = img.rotate(180, expand=True)
                            img.save(iter_path)
                            print(f'-- Rotated image \t{iter_bsn_ext} \tby 180 degrees clockwise.')
                            list_path_rotated.append(iter_path)
                        elif orientation == 6:
                            img = img.rotate(270, expand=True)
                            img.save(iter_path)
                            print(f'-- Rotated image \t{iter_bsn_ext} \tby 90 degrees clockwise.')
                            list_path_rotated.append(iter_path)
                        elif orientation == 8:
                            img = img.rotate(90, expand=True)
                            img.save(iter_path)
                            print(f'-- Rotated image \t{iter_bsn_ext} \tby 270 degrees clockwise.')
                            list_path_rotated.append(iter_path)
                        else:
                            print(f'-- File \t{iter_bsn_ext}\t has the right orientation and doesn\'t need to be changed.')
                    else:
                        print(f'-- File \t{iter_bsn_ext} \thas no orientation information.')
            except Exception as e:
                print(f'-- Error processing file \t{iter_bsn_ext}: \t{e}')
    
    #[12] Return the list of rotated image paths
    print(f'-- rotated {len(list_path_rotated)} images.')
    return list_path_rotated








def fix_corrupted_image_files(list_path_file, suffix='_fixed', verbose=True):
    """
    Attempts to open and re-save each image file to fix potential corruption.
    """
    allowed_ext = ['.jpg', '.jpeg', '.png']
    list_path_fixed = []

    for path in list_path_file:
        ext = os.path.splitext(path)[1].lower()
        if ext not in allowed_ext:
            if verbose:
                print(f'[skip] Not an image: {path}')
            continue

        try:
            img = Image.open(path)
            img.verify()  # Quick check for corruption
            img = Image.open(path).convert('RGB')  # Reload for saving
            if suffix is None:
                path_fixed = path
                img.save(path_fixed, format=img.format)
            else:
                path_fixed = f'{os.path.splitext(path)[0]}{suffix}.jpg'
                img.save(path_fixed, format='JPEG')
            list_path_fixed.append(path_fixed)
            if verbose:
                print(f'[ok] Fixed and saved: {path_fixed}')

        except Exception as e:
            if verbose:
                print(f'[fail] Cannot fix: {path}\n    Error: {e}')

    return list_path_fixed













#[4] Image - End
 











