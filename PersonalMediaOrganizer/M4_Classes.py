"""
[MDS_M4_Classes]
Purpose: Check the device for the LMS system.
Author: Meng-Chi Ed Chen
Date: 2024-0613

Status: Complete.
"""
import os, sys, time, glob, re, cv2, shutil
from datetime import datetime
from tabulate import tabulate
from tkinter.filedialog import askdirectory
import numpy as np

import os, sys, time
from PersonalMediaOrganizer import M1_Files as M1F
from PersonalMediaOrganizer import M3_Image as M3I
import pandas as pd


def print_aligned_strings(str1, str2, total_width=60, end='\n'):
    """
    Prints two strings with the second aligned to the right, separated by at least 2 spaces within the total width.
    """
    min_space = 2
    str2_start = max(total_width - len(str1), min_space)
    str_out = f'{str1}{" "*str2_start}{str2}'
    print(str_out, end=end)



class MediaSortingManager:
    def __init__(self):
        #[1] Ask folder location
        print('\nWelcome to Media Date Sorting.\nLet us turn your mements into memories.')
        self.dir_sort = askdirectory(title='Select Folder')
        self.dir_bsn = os.path.basename(self.dir_sort)
        
        #[2] Start text report.
        self.timestamp = datetime.now().strftime("%Y-%m%d-%H%M%S")
        self.text_report = f'{self.timestamp}\n\nDirectory: {self.dir_sort}\n\n\n'
        print(self.text_report)
        
        #[4] Reset files from previous runs if needed.
        M1F.check_folder_and_reset_files(   self.dir_sort, 
                                            kwd_test_run_folder = ['01_AAE', '02_HEIC', '03_Dup'], 
                                            replace_with_bkup   = False,
                                            remove_date_tag     = False,
                                            keep_only_HEIC      = True,
                                            exit_after_reset    = True)

    def dump_AAE_files(self):
        list_paths, list_bsn \
            = M1F.batch_file_relocate(self.dir_sort, ['.AAE'], [], '01_AAE', print_bsn=False)
        text_3 = f'[AEE] There are {len(list_bsn)} AEE files.\n\n\n'
        self.text_report += text_3

    def convert_HEIC_to_JPG(self):
        list_paths, list_error \
            = M3I.convert_HEIC_to_JPG_and_keep_EXIF_info(self.dir_sort, 
                                                         delete_or_remove=False, 
                                                         print_status=True, 
                                                         dump_dir_name='02_HEIC')
        #input(f'\nlist_paths:\n{list_paths}\nPress Enter to continue...' )
        text_error = '\n'.join(list_error)
        text_4 = f'[HEIC] There are {len(list_paths)} HEIC files. \nHEIC conversion error ({len(list_error)}):\n{text_error}\n--\n'
        self.text_report += text_4

    def filter_media_files(self):
        list_kwd_yes_or_1 = ['.png', '.PNG', '.jpg', '.JPG', '.gif', '.GIF', 'mov', 'MOV', 'mp4', 'MP4']
        list_kwd_no_or_1 = ['.txt', '.HEIC', '.bat']
        self.list_path_media, self.list_bns_media \
            = M1F.filter_file_in_dir_with_keywords(
            self.dir_sort, list_kwd_yes_or_1, list_kwd_no_or_1, False)
        text_5 = f'[Media] There are {len(self.list_bns_media)} media files. (PNG, JPG, GIF, or MOV)\n\n\n'
        self.text_report += text_5

    def organize_files_by_date(self):
        self.list_media_datetime, self.list_media_ext, self.list_method \
            = M3I.retrieve_datetime_from_list_of_media_files(
            self.list_path_media, print_status=True, datetime_format='%Y-%m-%d, %H:%M:%S')
        self.list_result = M3I.move_media_files_into_date_folders(
            self.list_path_media, self.list_media_datetime, print_status=True)

    def search_large_files(self, mb_limit=10):
        df_report, sum_oversize = M1F.file_type_statistic_in_dir_and_subdir(self.dir_sort, mb_limit, save_txt=False)
        str_df_report = tabulate(df_report, headers='keys', tablefmt='orgtbl')
        text_10 = f'[Large] There are {sum_oversize} files over {mb_limit} Mb. \nPlease review them to save space.\n\n{str_df_report}\n\n\n'
        self.text_report += text_10

    def save_report(self):
        path_report = os.path.join(self.dir_sort, f'{self.timestamp}_[{self.dir_bsn}].txt')
        M1F.create_txt_and_save_text(path_report, self.text_report, open_file=True)

    def run_all(self):
        self.dump_AAE_files()
        self.convert_HEIC_to_JPG()
        self.filter_media_files()
        self.organize_files_by_date()
        self.search_large_files()
        self.save_report()
        print('\nComplete "MediaSortingManager".')




class AddDateToFileNameManager:
    def __init__(   self, 
                    dir_work,
                    skip_bar_bsn = 3,
                    skip_udsc_bsn = 3):
        """
        skip_bar_bsn: If see bar "-" in the first 3 characters of the base file name, skip the file.
        skip_udsc_bsn: If see underscore "_" in the first 3 characters of the base file name, skip the file.
        """
        
        #[1] Initialize
        print(f'\nWelcome to Add Date to File Name Tool.\nLet us add date info to your media file names.\ndir_work: {dir_work}')

        #[2] Regist instance variables.
        self.dir_work = dir_work
        self.datetime_format = '%Y-%m%d'  # Default date format.
        self.skip_bar_bsn = skip_bar_bsn
        self.skip_udsc_bsn = skip_udsc_bsn
        self.list_bsn = []
        self.cnt_to_process = 0
        self.df_files = None
        self.preview_rows = 10
        
        #[4] Reset files from previous runs if needed.
        M1F.check_folder_and_reset_files(   self.dir_work, 
                                            kwd_test_run_folder = ['09_bkup'], 
                                            replace_with_bkup   = True,
                                            remove_date_tag     = False,
                                            keep_only_HEIC      = False,
                                            exit_after_reset    = False)

        #[5] Prepare to porcess.
        self.ask_short_or_long_date_format()
        self.get_list_of_files_to_process()


    def ask_short_or_long_date_format(self):
        question_message = '\nWould you like to use short date format (YYYY-MMDD_) or long date format (YYYY-MMDD-HHMM_)? \n'\
                            'Enter "S" for short or "L" for long:\n'
        input = M1F.ask_for_input(question_message, readback=True, allow_empty=False)
        
        #[2] Determine date format.
        if input.lower() in ['s', 'short', '']:
            self.datetime_format = '%Y-%m%d'
        elif input.lower() in ['l', 'long']:
            self.datetime_format = '%Y-%m%d-%H%M'



    def construct_new_file_name(self, bsn_file, media_datetime):

        #[2] Determine the date pattern to check based on datetime format
        if self.datetime_format == '%Y-%m%d':
            pattern = r'^\d{4}-\d{4}_'
            the_other_pattern = r'^\d{4}-\d{4}-\d{4}_'
        elif self.datetime_format == '%Y-%m%d-%H%M':
            pattern = r'^\d{4}-\d{4}-\d{4}_'
            the_other_pattern = r'^\d{4}-\d{4}_'
        else:
            pattern = None
            
        #[4] Remove the_other_pattern if exists
        if the_other_pattern and re.match(the_other_pattern, bsn_file):
            bsn_file = re.sub(the_other_pattern, '', bsn_file)  
        
        return f'{media_datetime}_{bsn_file}'
            


    def get_list_of_files_to_process(self):
        #[1] Prepare file lists and create processed directory, ignoring .JPG
        allowed_media_ext = ['.avif', '.heic', '.webp', '.tif', '.tiff', '.bmp', 
                            '.jpeg', '.jpg', '.png', '.gif',
                            '.mp4', '.mov', '.avi', '.mkv', '.m4v']
        list_path, _ = M1F.filter_files_by_extension(   self.dir_work, 
                                                        list_ext            = allowed_media_ext,
                                                        include_or_exclude  = 'include', 
                                                        remove_file         = False)
        self.list_bsn = [ os.path.basename(path) for path in list_path ]

        #[2] Determine the date pattern to check based on datetime format
        if self.datetime_format == '%Y-%m%d':
            pattern = r'^\d{4}-\d{4}_'
        elif self.datetime_format == '%Y-%m%d-%H%M':
            pattern = r'^\d{4}-\d{4}-\d{4}_'
        else:
            pattern = None
            
        #[3] Filter files and build list of paths to process
        self.list_path_to_process   = []
        self.list_bsn_to_process    = []
        self.list_path_new  = []
        self.list_bsn_new   = []
        total_width = 50
        
        for bsn_file in self.list_bsn:
            #[4] Skip if file already has the desired date format
            if pattern and re.match(pattern, bsn_file):
                print_aligned_strings(f'-- Skip: {bsn_file}.', 'Already has required date format.', total_width)
                continue
            
            #[5] Skip if file has "-" in the first few characters
            if '-' in bsn_file[:self.skip_bar_bsn]:
                print_aligned_strings(f'-- Skip: {bsn_file}.', 'Has "-".', total_width)
                continue
            
            #[6] Skip if file has "_" in the first few characters
            if '_' in bsn_file[:self.skip_udsc_bsn]:
                print_aligned_strings(f'-- Skip: {bsn_file}.', 'Has "_".', total_width)
                continue
            
            #[7] If all checks passed, put up the new file name for preview.
            path_to_process =  os.path.join(self.dir_work, bsn_file)
            ext, media_datetime, method \
                = M3I.retrieve_datetime_of_single_media_files(path_to_process, self.datetime_format)
            bsn_new = self.construct_new_file_name(bsn_file, media_datetime)
            path_new = os.path.join(self.dir_work, bsn_new)
            
            #[8] Send warning if path_new already exists
            if os.path.exists(path_new):
                print_aligned_strings(f'-- Warning: {bsn_file}.', f'New file name {bsn_new} already exists! (Skip)', total_width)
                continue
            
            #[10] File passed all filters - add to processing list
            self.list_path_to_process.append(os.path.join(self.dir_work, bsn_file))
            self.list_bsn_to_process.append(bsn_file)
            self.list_path_new.append(path_new)
            self.list_bsn_new.append(bsn_new)

        #[11] Update list_bsn to only contain files that will be processed
        self.cnt_to_process = len(self.list_path_to_process)
        self.df_files = pd.DataFrame({  'Original Base Name': self.list_bsn_to_process,
                                        'New Base Name': self.list_bsn_new,
                                        'Original Path': self.list_path_to_process,
                                        'New Path': self.list_path_new})
        df_preview = self.df_files[['Original Base Name', 'New Base Name']].head(self.preview_rows)
        text_preview = f'-- Total files to process {self.cnt_to_process}. Preview top {self.preview_rows}:\n{tabulate(df_preview, headers="keys", tablefmt="orgtbl")}'
        print(text_preview)
        
        #[12] Ask user to confirm
        str_continue = M1F.ask_for_input('The above is the preview. Do you want to continue? (Close the program to exit):\n'
                                 , readback=True, allow_empty = False)
        if str_continue.lower() in ['y', 'yes', 'yeah', 'ok', 'okey', 'aff', 'affirmative']:
            #[13] Perform the replacement.
            self.rename_files(print_status=True)
        else:
            print('No affirmative answer detected. Exiting...')
            sys.exit(0)

        
    def rename_files(self, print_status=True):
        #[1] Prepare lists
        list_path_old = self.df_files['Original Path'].tolist()
        list_path_new = self.df_files['New Path'].tolist()
        
        #[2] Rename files
        for i in range(self.cnt_to_process):
            path_old = list_path_old[i]
            path_new = list_path_new[i]
            os.rename(path_old, path_new)
            if print_status:
                print_aligned_strings(f'[{i+1:03d}/{self.cnt_to_process:03d}] Renamed: {os.path.basename(path_old)}  -->  ', 
                                      f'{os.path.basename(path_new)}', 
                                      total_width=80)








class ExtendEdgeManager:
    """
    Extend the edges of an image to achieve a desired aspect ratio by adding borders.
    """
    def __init__(self,
                dir_work,
                ext_method          = 'multiples_of',
                ext_value           = 50,
                tag_processed       = 'edge',
                original_folder     = '01_Original'
                ):
        #[1] Register instance variables.
        self.dir_work = dir_work
        self.ext_method = ext_method
        self.ext_value = ext_value
        self.tag_processed = tag_processed
        self.most_frequent_color = [255, 255, 255]  # Default white background
        self.original_folder = original_folder
        
        
        #[4] Reset files from previous runs if needed.
        M1F.check_folder_and_reset_files(   self.dir_work, 
                                            kwd_test_run_folder = ['01_Original'], 
                                            replace_with_bkup   = True,
                                            remove_date_tag     = False,
                                            keep_only_HEIC      = False,
                                            exit_after_reset    = False)
        
        
        M1F.make_dir_if_not_exist(os.path.join(self.dir_work, self.original_folder))
        
        #[5] Find image paths in dir_work.
        allow_exts = ['png', 'jpg', 'jpeg', 'png', 'tiff', 'bmp', 'gif']
        list_kwd_exclude = ['edge']
        self.list_img_paths, self.list_img_bsns, _ = M1F.find_list_exts_in_dir(self.dir_work, allow_exts, list_kwd_exclude)
        
        
        
        
        print('[self.list_img_bsns]:\n' + '\n'.join(self.list_img_bsns))
        
        
    def batch_image_extend_edge(self):
        print(f'\n[batch_image_extend_edge]')
        
        
        #[5] Loop through each image and extend edges.
        cnt_total = len(self.list_img_paths)
        for i, i_img_paths in enumerate(self.list_img_paths):
            #[1]
            print(f'\n[{i+1:02d}/{cnt_total:02d}] {os.path.basename(i_img_paths)}')
            
            #[3] Read image and get basic info.
            i_arrimg = cv2.imread(i_img_paths)
            if self.check_if_pure_color_edges_exist(i_arrimg) is True:
                continue
            h, w = i_arrimg.shape[:2]
            #self.find_background_color(i_arrimg)
            
            #[4] Determine extension amounts and pad image.
            hl_ext, hr_ext, wb_ext, wt_ext \
                = self.edge_extension_amount(h, w, self.ext_method, self.ext_value)
            i_arrimg_edge = self.pad_image_with_color(i_arrimg, hl_ext, hr_ext, wb_ext, wt_ext)
            
            #[5] Save the extended image.
            bsnext_output = f'{os.path.splitext(os.path.basename(i_img_paths))[0]}_{self.tag_processed}.jpg'
            path_save = os.path.join(self.dir_work, bsnext_output)
            cv2.imwrite(path_save, i_arrimg_edge)
            
            #[6] Move original image to original_folder.
            path_move_to = os.path.join(self.dir_work, self.original_folder, os.path.basename(i_img_paths))
            shutil.move(i_img_paths, path_move_to)

                        
    
    def check_if_pure_color_edges_exist(self, arrimg):
        """
        Compute the std of left, right, top, bottom 3 pxiels of rows and columns.
        If the std is very low (e.g., < 5), consider that edge is already padded.
        """
        h, w = arrimg.shape[:2]
        edge_width = 3
        std_threshold = 5
        
        #[1] Left edge
        left_edge = arrimg[:, :edge_width, :].reshape(-1, 3)
        left_std = np.std(left_edge, axis=0)
        
        #[2] Right edge
        right_edge = arrimg[:, -edge_width:, :].reshape(-1, 3)
        right_std = np.std(right_edge, axis=0)
        
        #[3] Top edge
        top_edge = arrimg[:edge_width, :, :].reshape(-1, 3)
        top_std = np.std(top_edge, axis=0)
        
        #[4] Bottom edge
        bottom_edge = arrimg[-edge_width:, :, :].reshape(-1, 3)
        bottom_std = np.std(bottom_edge, axis=0)
        
        #[5] Check if any edge has std below threshold
        edges_std = {
            'left':     [left_std,      np.mean(left_std)],
            'right':    [right_std,     np.mean(right_std)],
            'top':      [top_std,       np.mean(top_std)],
            'bottom':   [bottom_std,    np.mean(bottom_std)]}
        for edge, std_values in edges_std.items():
            print_aligned_strings(f'   {edge}:', f'{std_values[1]:.2f}', 20)
        
        #[6] Determine if all edges are padded
        if edges_std['left'][1] < std_threshold and edges_std['right'][1] < std_threshold:
            print(f'-- Image already padded on left and right edges for at least {edge_width} pixels.')
            return True
        elif edges_std['top'][1] < std_threshold and edges_std['bottom'][1] < std_threshold:
            print(f'-- Image already padded on top and bottom edges for at least {edge_width} pixels.')
            return True

        #[7] Report edges that are not padded
        print(f'-- Image not padded on every edges for at least {edge_width} pixels.')
        
        return False
            
    

    def find_background_color(self, arrimg):
        print(f'\n[find_background_color]')
        """
        Randomly sample 1000 pixels from any location.
        Find the most frequent color among the sampled pixels.
        Return that color as the background color.
        """
        #[1] Reshape image to a list of pixels
        pixels = arrimg.reshape(-1, arrimg.shape[2])
        #[2] Randomly sample 1000 pixels
        num_samples = min(1000, len(pixels))
        sampled_indices = np.random.choice(len(pixels), num_samples, replace=False)
        sampled_pixels = pixels[sampled_indices]
        #[3] Find the most frequent color
        colors, counts = np.unique(sampled_pixels, axis=0, return_counts=True)
        self.most_frequent_color = colors[np.argmax(counts)]
        print(f'-- Most frequent color (BGR):   {self.most_frequent_color}')
        return self.most_frequent_color
    
    
    def edge_extension_amount(self, h_org, w_org, method='fixed_pixel', value=5):
        
        list_allowed_methods = ['fixed_pixel']
        
        #[1] Determine extension amounts based on method.
        if method == 'fixed_pixel':
            lw_ext, rw_ext, bh_ext, th_ext = value, value, value, value
            
        elif method == 'proportional':
            if value <= 1:
                raise ValueError('For proportional method, value should be greater than 1 (e.g., 1.2 for 20% increase).')
            aspect_ratio = w_org / h_org
            h_new = int(h_org * value)
            w_new = int(h_new * aspect_ratio)
            total_h_ext = h_new - h_org
            total_w_ext = w_new - w_org
            lw_ext, rw_ext = total_w_ext // 2, total_w_ext - (total_w_ext // 2)
            bh_ext, th_ext = total_h_ext // 2, total_h_ext - (total_h_ext // 2)
                
        elif method == 'multiples_of':
            #[1] Find the next multiple of value for both dimensions.
            h_new = ((h_org + value - 1) // value) * value
            w_new = ((w_org + value - 1) // value) * value
            
            #[2] Divided the difference by 2 for each side.
            lw_ext, rw_ext  = (w_new - w_org) // 2, (w_new - w_org) - (w_new - w_org) // 2
            bh_ext, th_ext = (h_new - h_org) // 2, (h_new - h_org) - (h_new - h_org) // 2
            
        elif method == '4x6photo':
            target_aspect_ratio = 4 / 6
            print(f'-- Target aspect ratio:         {target_aspect_ratio:.4f} (4:6)')
            
            
            #[1] Determin the orientation of the image.
            if w_org > h_org:
                orient = 'landscape'
                original_aspect_ratio = h_org / w_org
            elif w_org < h_org:
                orient = 'portrait'
                original_aspect_ratio = w_org / h_org
            else:
                orient = 'landscape'  # Treat square as landscape
                original_aspect_ratio = 1.0
            print(f'-- Original aspect ratio:       {original_aspect_ratio:.4f} ({orient})')
            
            #[2] Image is wider than 4:6 (long edge too short). 
            if original_aspect_ratio > target_aspect_ratio:
                #[3] Keep height, calculate new width to achieve 4:6 ratio
                if orient == 'landscape': # Width is the long edge.
                    h_new = h_org
                    bh_ext, th_ext = 0, 0
                    w_new = int(h_org / target_aspect_ratio)
                    lw_ext = (w_new - w_org) // 2
                    rw_ext = (w_new - w_org) - lw_ext
                #[4] Keep width, calculate new height to achieve 4:6 ratio
                elif orient == 'portrait':  # Height is the long edge.
                    w_new = w_org
                    lw_ext, rw_ext = 0, 0
                    h_new = int(w_org / target_aspect_ratio)
                    bh_ext = (h_new - h_org) // 2
                    th_ext = (h_new - h_org) - bh_ext
            #[7] Image is taller than 4:6 (short edge too short).
            elif original_aspect_ratio < target_aspect_ratio:
                #[8] Keep width, calculate new width to achieve 4:6 ratio
                if orient == 'landscape': # Width is the long edge. (Image is flat and wide.)
                    w_new = w_org
                    lw_ext, rw_ext = 0, 0
                    h_new = int(w_org * target_aspect_ratio)
                    bh_ext = (h_new - h_org) // 2
                    th_ext = (h_new - h_org) - bh_ext
                #[9] Keep height, calculate new height to achieve 4:6 ratio
                elif orient == 'portrait':  # Height is the long edge. (Image is thin and tall.)
                    h_new = h_org
                    bh_ext, th_ext = 0, 0
                    w_new = int(h_org * target_aspect_ratio)
                    lw_ext = (w_new - w_org) // 2
                    rw_ext = (w_new - w_org) - lw_ext
                
        
        #[8] Report.
        """
        lw_ext: left width extension
        rw_ext: right width extension
        bh_ext: bottom height extension
        th_ext: top height extension      
        """
        h_new = h_org + bh_ext + th_ext
        w_new = w_org + lw_ext + rw_ext
        new_aspect = min(w_new / h_new, h_new / w_new)
        text_rpt =  f'-- Original (h, w):             {h_org} × {w_org}\n'\
                    f'-- Extension (hl, hr, wb, wt):  ({lw_ext}, {rw_ext}, {bh_ext}, {th_ext})\n'\
                    f'-- New Size (h_new, w_new):     {h_new} × {w_new} ({new_aspect:.4f}))\n'
        print(text_rpt)
        
        
        if lw_ext < 0 or rw_ext < 0 or bh_ext < 0 or th_ext < 0:
            raise ValueError('Negative extension values detected.')
        return lw_ext, rw_ext, bh_ext, th_ext
    
    
    def pad_image_with_color(self, arrimg, hl_ext, hr_ext, wb_ext, wt_ext, bkgd_color=None):
        print(f'\n[pad_image_with_color]')
        if bkgd_color is None:
            bkgd_color = self.most_frequent_color
        #[1] Pad the image with specified color.
        arrimg_padded = cv2.copyMakeBorder(
            arrimg,
            top         = wt_ext,
            bottom      = wb_ext,
            left        = hl_ext,
            right       = hr_ext,
            borderType  = cv2.BORDER_CONSTANT,
            value       = tuple(int(c) for c in bkgd_color)
        )
        return arrimg_padded
    
    
    



class AddTimestampManager:
    """
    Add timestamp to images files.
        
    """

    def __init__(self,
                dir_work,
                dt_source           = 'filename',
                location            = 'top-left',
                put_on_padding      = True,
                ):
        #[1] Register instance variables.
        self.dir_work       = dir_work
        self.dt_source      = dt_source
        self.location       = location
        self.put_on_padding = put_on_padding
        self.preview_rows   = 10
        self.list_img_paths     = []
        self.list_img_bsns      = []
        self.list_timestamp_str = []
        
        #[4] Reset files from previous runs if needed.
    
        M1F.check_folder_and_reset_files(   self.dir_work, 
                                            kwd_test_run_folder = ['01_Original'], 
                                            replace_with_bkup   = True,
                                            remove_date_tag     = False,
                                            keep_only_HEIC      = False,
                                            exit_after_reset    = False)
        
                
        #[5] Find image paths in dir_work.
        allow_exts = ['png', 'jpg', 'jpeg', 'png', 'tiff', 'bmp', 'gif']
        list_kwd_exclude = ['bat', 'ts']
        self.list_img_paths, self.list_img_bsns, self.cnt_total \
            = M1F.find_list_exts_in_dir(self.dir_work, allow_exts, list_kwd_exclude)
        
        
        
        #[6] Gather datetime info.
        self.gather_datetime_info()
        
        #[7] Batch add timestamps to images.
        self.batch_add_timestamps_to_images()

    def gather_datetime_info(self):
        """
        Gather datetime info from file names and EXIF data.
        """
        #[1] Validate dt_source
        allow_dt_source = ['filename', 'exif_datetime', 'cross_check']
        if self.dt_source not in allow_dt_source:
            raise ValueError(f'dt_source should be one of {allow_dt_source}.')
        
        
        #[2] Loop through each image and gather datetime info.
        for i, i_bsn in enumerate(self.list_img_bsns):
            
            prefix = i_bsn.split('_')[0]
            need_nl = True      # Check if need new line after print.
            
            #[3] Convert prefix to datetime string based on format.
            # Format: YYYY-MMDD or YYYY-MMDD-HHMM
            dt_string = self.convert_prefix_to_datetime_string(prefix)
            print_aligned_strings(f'[{i+1:02d}/{self.cnt_total:02d}] prefix: {prefix}', 
                                  f'--> dt_string: {dt_string}.', total_width=40, end='')
            
            #[4] Cross-check with EXIF datetime if needed.
            if self.dt_source == 'exif_datetime' or self.dt_source == 'cross_check':
                path_img = os.path.join(self.dir_work, i_bsn)
                exif_dt_string = M3I.retrieve_datetime_of_single_media_files(path_img, datetime_format='%Y-%m-%d, %H:%M:%S')
                if self.dt_source == 'exif_datetime':
                    dt_string = exif_dt_string[1]
                elif self.dt_source == 'cross_check':
                    if dt_string is None:
                        dt_string = exif_dt_string[1]
                    else:
                        #[1] If the dt_string only have  missing second(ss) part.
                        if len(dt_string) < len(exif_dt_string[1]):
                            if dt_string == exif_dt_string[1][:-3]:
                                print(f' Using EXIF {exif_dt_string[1]}')
                                need_nl = False
                                dt_string = exif_dt_string[1]
                        elif exif_dt_string[1] and dt_string != exif_dt_string[1]:
                            print(f'-- Warning: Mismatch datetime. Using EXIF {exif_dt_string[1]}')
                            need_nl = False
                            dt_string = exif_dt_string[1]
                        
            if need_nl:
                print()
            self.list_timestamp_str.append(dt_string)
            
            

            
        #[11] Organize into DataFrame for preview.
        self.df_files = pd.DataFrame({  'Path': self.list_img_paths,
                                        'Base Name': self.list_img_bsns,
                                        'Timestamp': self.list_timestamp_str})
        df_preview = self.df_files[['Base Name', 'Timestamp']].head(self.preview_rows)
        text_preview = f'-- Total files to process {self.cnt_total}. Preview top {self.preview_rows}:\n{tabulate(df_preview, headers="keys", tablefmt="orgtbl")}'
        print(text_preview)
        
    
    def batch_add_timestamps_to_images(self):
        """
        Iterate through self.df_files to add timestamp text on images.
        """

        def _determine_text_details(pad_size, loc_text, i_arrimg):
            #[1] Font Scale (f_scl)
            f_scl_thrds = [(200, 3.0), (150, 2.0), (100, 1.0)]
            f_scl = next((scale for threshold, scale in f_scl_thrds if pad_size >= threshold), 1.0)
            
            #[2] Font Thickness (f_thk)
            f_thk_thrds = [(200, 4), (150, 3), (100, 2)]
            f_thk = next((thick for threshold, thick in f_thk_thrds if pad_size >= threshold), 1)
            
            #[3] Character Height (char_height)
            char_height = int(cv2.getTextSize('A', f_fac, f_scl, f_thk)[0][1])
            
            #[4] Location (coord_xy)
            if loc_text == 'top&bottom':
                if pad_size < char_height * 4:
                    coord_xy = (int(1.2 * char_height), int(i_arrimg.shape[0] - 0.5 * pad_size + 0.6 * char_height))
                else:
                    coord_xy = (int(1.2 * char_height), int(i_arrimg.shape[0] - 1.7 * char_height))
            elif loc_text == 'left&right':
                if pad_size < char_height * 4:
                    coord_xy = (int(1.2 * char_height), int(i_arrimg.shape[1] - 0.5 * pad_size + 0.6 * char_height))
                else:
                    coord_xy = (int(1.2 * char_height), int(i_arrimg.shape[1] - 1.7 * char_height))      
            else:
                raise ValueError(f'Unknown loc_text: {loc_text}.')
            return f_scl, f_thk, char_height, coord_xy
            
        f_fac = cv2.FONT_HERSHEY_SIMPLEX
        f_clr = (64, 64, 64)  # Black color
        
        for i in range(self.cnt_total):
            path_img = self.df_files.at[i, 'Path']
            bsn_img = self.df_files.at[i, 'Base Name']
            timestamp_str = self.df_files.at[i, 'Timestamp']
            
            #[1] Read image and locate edge padding
            i_arrimg = cv2.imread(path_img)
            #loc_text, px_pad, that_edge, the_other_edge = self.locate_edge_and_illustrate_padding(i_arrimg)
            loc_text, pad_size = self.locate_edge_and_illustrate_padding(i_arrimg)
            f_scl, f_thk, char_height, coord_xy = _determine_text_details(pad_size, loc_text, i_arrimg)
            text_size_info =    f'-- loc_text: {loc_text}, pad_size: {pad_size}.\n'\
                                f'-- (f_scl, f_thk, coord_xy, char_height): ({f_scl}, {f_thk}, {coord_xy}, {char_height})'
            print(text_size_info)
            #[2] Determine text location
            if loc_text == 'top&bottom':
                arrimg_with_text = add_text_on_image( i_arrimg,
                                                      str_text          = timestamp_str,
                                                        coord_xy        = coord_xy,
                                                        text_direction  = 'horizontal',
                                                        add_both_sides  = True,
                                                        fontFace        = f_fac,
                                                        font_scale      = f_scl,
                                                        color           = f_clr,
                                                        thickness       = f_thk,
                                                        smooth_iterations=3)
            
            #[2] Add text on image
            elif loc_text == 'left&right':
                
                arrimg_with_text = add_text_on_image( i_arrimg,
                                                    str_text        = timestamp_str,
                                                    coord_xy        = coord_xy,
                                                    text_direction  = 'vertical',
                                                    add_both_sides  = True,
                                                    fontFace        = f_fac,
                                                    font_scale      = f_scl,
                                                    color           = f_clr,
                                                    thickness       = f_thk,
                                                    smooth_iterations=3)
                
            else:
                raise ValueError(f'Unknown loc_text: {loc_text}.')
                
            #[3] Save image with new name
            bsnext_output = f'{os.path.splitext(bsn_img)[0]}_ts.jpg'
            path_save = os.path.join(self.dir_work, bsnext_output)
            cv2.imwrite(path_save, arrimg_with_text)
            print_aligned_strings(f'[{i+1:02d}/{self.cnt_total:02d}] Saved: {bsnext_output}', '', total_width=60)
            
    
    

    @staticmethod
    def locate_edge_and_illustrate_padding(arrimg):
        """
        Check how much white padding exists on each edge of the image.
        Return: str_loc, px_padding, that_edge_length, the_other_edge_length
        Follow Bounding Box Convention (LTRB).
        """
        h, w = arrimg.shape[:2]
        print(f'\n[locate_edge_and_illustrate_padding] h × w: {h} × {w}')
        
        #[1] Column-wise and row-wise
        col_avg = np.mean(arrimg, axis=0)  # Shape: (w, 3)
        left_pad , rightpad = array_index_match(col_avg, np.array([255, 255, 255]))
        row_avg = np.mean(arrimg, axis=1)  # Shape: (h, 3)
        top_pad, bottom_pad = array_index_match(row_avg, np.array([255, 255, 255]))
        
        #[3] Display padding as a 3x3 grid
        df_pad = pd.DataFrame([
            ['--',      top_pad,    '--'    ],
            [left_pad,  '--',       rightpad],
            ['--',      bottom_pad, '--'    ]])
        print(f'{tabulate(df_pad, headers=[], showindex=False, tablefmt="plain")}\n')
        
        
        #[5] Collect for return.
        list_pads = [left_pad, top_pad, rightpad, bottom_pad]
        list_h_w = [h, w]
        if list_pads[0] == 0 and list_pads[2] == 0:
            loc_text = 'top&bottom'
            pad_size = min(list_pads[1], list_pads[3])
        elif list_pads[1] == 0 and list_pads[3] == 0:
            loc_text = 'left&right'
            pad_size = min(list_pads[0], list_pads[2])
        else:
            raise ValueError(   'I don\'t know what would happen here, \n'\
                                'so let\'s raise an error and figure it out later.')
            
        return loc_text, pad_size



    def convert_prefix_to_datetime_string(self, prefix):
        """
        Convert filename prefix to datetime string.
        2024-1204-124813 -> 2024-12-04, 12:48:13
        2024-1204-1248 -> 2024-12-04, 12:48
        2024-1204 -> 2024-12-04
        """
        # Pattern 1: YYYY-MMDD-HHMM (with time)
        if re.match(r'^\d{4}-\d{4}-\d{4}-\d{2}$', prefix):
            year = prefix[0:4]
            month = prefix[5:7]
            day = prefix[7:9]
            hour = prefix[10:12]
            minute = prefix[12:14]
            second = prefix[14:16]
            return f'{year}-{month}-{day}, {hour}:{minute}:{second}'
        
        elif re.match(r'^\d{4}-\d{4}-\d{4}$', prefix):
            year = prefix[0:4]
            month = prefix[5:7]
            day = prefix[7:9]
            hour = prefix[10:12]
            minute = prefix[12:14]
            return f'{year}-{month}-{day}, {hour}:{minute}'
        
        # Pattern 2: YYYY-MMDD (without time)
        elif re.match(r'^\d{4}-\d{4}$', prefix):
            year = prefix[0:4]
            month = prefix[5:7]
            day = prefix[7:9]
            return f'{year}-{month}-{day}'
        
        else:
            #print(f'\n-- Warning: prefix "{prefix}" does not match expected format.')
            return None
        
        



def add_text_on_image_both_sides(   arrimg, str_text, coord_xy=(10, 30),
                                    text_direction='horizontal',
                                    fontFace = cv2.FONT_HERSHEY_SIMPLEX,
                                    font_scale=1.0, 
                                    color=(0, 0, 0), 
                                    thickness=2,
                                    smooth_iterations=3):
    if text_direction == 'left&right':
        #[1] Rotate image 90° counter-clockwise
        rotated = cv2.rotate(arrimg, cv2.ROTATE_90_CLOCKWISE)
        
        #[2] Map coordinates from original to rotated image
        new_x, new_y = coord_xy # We don't convert here.
        
        #[3] Put text normally on rotated image
        putTextSmooth(rotated, str_text, (new_x, new_y), 
                     fontFace, font_scale, color, thickness, smooth_iterations)
        
        #[4] Rotate back clockwise
        arrimg[:] = cv2.rotate(rotated, cv2.ROTATE_90_COUNTERCLOCKWISE)
    else: # top&bottom
        putTextSmooth(arrimg, str_text, coord_xy, 
                     fontFace, font_scale, color, thickness, smooth_iterations)
        
        #[1] Rotate image 180°.
        rotated = cv2.rotate(arrimg, cv2.ROTATE_180)
        
        
        
    
    return arrimg


def add_text_on_image(  arrimg, str_text, coord_xy=(10, 30),
                        text_direction='horizontal',
                        add_both_sides=True,
                        fontFace = cv2.FONT_HERSHEY_SIMPLEX,
                        font_scale=1.0, 
                        color=(0, 0, 0), 
                        thickness=2,
                        smooth_iterations=3):
    """
    Add text to image with support for horizontal and vertical orientations.
    Uses smooth text rendering for better quality.
    
    Args:
        arrimg: numpy array image (BGR format from cv2)
        str_text: text to add
        coord_xy: (x, y) position
        text_direction: 'horizontal' or 'vertical' (90° counter-clockwise rotation)
        font_scale: font size
        color: BGR color tuple
        thickness: text thickness
        smooth_iterations: number of iterations for smooth text rendering
    """
    if text_direction == 'vertical':
        #[1] Rotate image 90° counter-clockwise
        rotated = cv2.rotate(arrimg, cv2.ROTATE_90_CLOCKWISE)
        
        #[2] Map coordinates from original to rotated image
        new_x, new_y = coord_xy # We don't convert here.
        
        #[3] Put text normally on rotated image
        putTextSmooth(rotated, str_text, (new_x, new_y), 
                     fontFace, font_scale, color, thickness, smooth_iterations)
        
        if add_both_sides:
            #[1] Rotate, add text, rotate back 180°
            rotated_180 = cv2.rotate(rotated, cv2.ROTATE_180)
            putTextSmooth(rotated_180, str_text, (new_x, new_y), 
                     fontFace, font_scale, color, thickness, smooth_iterations)
            rotated[:] = cv2.rotate(rotated_180, cv2.ROTATE_180)
        
        #[4] Rotate back clockwise
        arrimg[:] = cv2.rotate(rotated, cv2.ROTATE_90_COUNTERCLOCKWISE)
    else:
        putTextSmooth(arrimg, str_text, coord_xy, 
                     fontFace, font_scale, color, thickness, smooth_iterations)
        
        if add_both_sides:
            #[1] Rotate, add text, rotate back 180°
            rotated = cv2.rotate(arrimg, cv2.ROTATE_180)
            putTextSmooth(rotated, str_text, coord_xy, 
                     fontFace, font_scale, color, thickness, smooth_iterations)
            arrimg[:] = cv2.rotate(rotated, cv2.ROTATE_180)
        
    return arrimg

def putTextSmooth(image, str_text, org, fontFace, fontScale, color, thickness, smooth_iterations=3):
    for i in range(smooth_iterations):
        t = max(1, thickness - i)  # Ensure thickness is at least 1
        cv2.putText(image, str_text, org, fontFace, fontScale, color, t, cv2.LINE_AA)










def array_index_match(arr_2d, arr_target, match_thrd = 20):
    """
    Find the indices of elements in a 2D array that match the target value.
    Cannot use direct comparison due to image compression errors.
    Direct comparison:      -- len_arr_2d: 3528, num_front_matches: 239, num_back_matches: 248
    Indirect comparison:    -- len_arr_2d: 3528, num_front_matches: 252, num_back_matches: 252
    The number is larger and two sides are balanced.
    """
    #[1] Shape validation
    if arr_target.ndim != 1:
        raise ValueError('arr_target should be a 1D array.')
    if arr_2d.shape[1] < 1 != arr_target.shape[0]:
        raise ValueError('arr_target should have the same number of columns as arr_2d.')
    
    #[2] Settings and initialization
    num_front_matches, num_back_matches = 0, 0
    len_arr_2d = arr_2d.shape[0]
    perfect_match = 0
    
    #[3] Count front matches
    for i in range(len_arr_2d):
        row_values = np.array(arr_2d[i, :].tolist())
        diff = np.mean(np.abs(row_values - arr_target))
        if diff < match_thrd:
            num_front_matches += 1
        else:
            break
        if diff > 0.5 * match_thrd:
            perfect_match += 1
    if perfect_match > 0:
        print(f'-- Warning: {perfect_match} imperfect matches detected in front matching.')

    #[4] Count back matches
    perfect_match = 0
    for j in range(len_arr_2d-1, -1, -1):
        row_values = np.array(arr_2d[j, :].tolist())
        diff = np.mean(np.abs(row_values - arr_target))
        if diff < match_thrd:
            num_back_matches += 1
        else:
            break
        if diff > 0.5 * match_thrd:
            perfect_match += 1
    if perfect_match > 0:
        print(f'-- Warning: {perfect_match} imperfect matches detected in back matching.')
    
    return num_front_matches, num_back_matches



