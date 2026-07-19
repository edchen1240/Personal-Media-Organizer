"""
[MDS_M4_Classes]
Purpose: Check the device for the LMS system.
Author: Meng-Chi Ed Chen
Date: 2024-0613

Status: Complete.
"""
import os, sys, time, glob, re, cv2, shutil
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from tabulate import tabulate
from tkinter.filedialog import askdirectory
import numpy as np

import os, sys, time
from PersonalMediaOrganizer import M0_Configuration as M0C
from PersonalMediaOrganizer import M1_Files as M1F
from PersonalMediaOrganizer import M3_Image as M3I
import pandas as pd





def register_date_folders(dir_media):
    """
    1. List all the folders in dir_media.
    2. Filter folders that match the date format YYYY-MM-DD.
    3. Report the folders that do not match the date format.
    4. State the total number of date folders found.
    
    """
    print(f'\n[register_date_folders]')
    #[1] List all folders in dir_media.
    list_all_folders = [f for f in os.listdir(dir_media) if os.path.isdir(os.path.join(dir_media, f))]
    
    #[2] Filter folders that match the date format YYYY-MM-DD.
    list_path_date_folders = [f for f in list_all_folders if re.match(r'^\d{4}-\d{2}-\d{2}$', f)]
    list_bsn_date_folders = [os.path.basename(f) for f in list_path_date_folders]
    
    #[3] Report the folders that do not match the date format.
    list_path_non_date_folders = [f for f in list_all_folders if f not in list_path_date_folders]
    if len(list_path_non_date_folders) > 0:
        list_bsn_non_date_folders = [os.path.basename(f) for f in list_path_non_date_folders]
        print(f'-- Found {len(list_bsn_non_date_folders)} folders that does not match YYYY-MM-DD. Here are the first 10:')
        for i_folder in list_bsn_non_date_folders[:10]:
            print(f'   {i_folder}')
    else:
        print('-- All folders match the date format YYYY-MM-DD.')
    
    #[4] State the total number of date folders found.
    text_report = f'-- Total date folders found: {len(list_path_date_folders)}\n'\
                  f'-- Ranging from {min(list_bsn_date_folders)} to {max(list_bsn_date_folders)}.'
    print(text_report)
    
    return list_path_date_folders, list_bsn_date_folders
    





class MediaFolderOverview:
    """
    Purpose: Provide an overview of media files in a folder, including counts and types.
    """
    
    def __init__(self, 
                    dir_media,
                    dir_output
                    ):
        #[1] Opening message.
        text_open = f'-- Initializing MediaFolderOverview for {dir_media}.\n'\
                    f'-- Output will be saved to {dir_output}.'
        print(text_open)
        
        #[2] Regist instance variables.
        self.dir_media  = dir_media
        self.dir_bsn    = os.path.basename(dir_media)
        self.dir_output = dir_output
        self.dts_scan   = datetime.now().strftime("%Y-%m%d-%H%M")   # When the folder scan ran.
        self.dts_stat   = self.dts_scan                             # When statistics were calculated (updated by calculate_statistics_summary).

        #[3] Register date folders.
        self.list_path_date_folders, self.list_bsn_date_folders = register_date_folders(dir_media)
        self.date_start = min(self.list_bsn_date_folders) if self.list_bsn_date_folders else None
        self.date_end   = max(self.list_bsn_date_folders) if self.list_bsn_date_folders else None
        self.days_covered = (datetime.strptime(self.date_end, "%Y-%m-%d") - datetime.strptime(self.date_start, "%Y-%m-%d")).days + 1 if self.date_start and self.date_end else None
        
        #[4] Define metadata dictionary to store information about the media folder overview.
        self.dict_meta = {  'Scan':                 self.dts_scan,
                            'Statistics':           None,
                            'dir_media':            self.dir_media,
                            'dir_bsn':              self.dir_bsn,
                            'dir_output':           self.dir_output,
                            'total_date_folders':   len(self.list_bsn_date_folders),
                            'date_start':           self.date_start,
                            'date_end':             self.date_end,
                            'days_covered':         self.days_covered,
                            'longest_gap_days':     None,
                            'longest_gap_start':    None,
                            'cnt_empty_folders':    None,
                            # Separators must NOT start with '=' — Excel treats that as a formula
                            # and repairs the workbook ("Removed Records: Formula from sheet1.xml").
                            '--- MFS ---':          '--- Media Folder Statistics ---',
                            'total_size_MB':        None,
                            'total_files':          None,
                            'total_image_files':    None,
                            'total_video_files':    None,
                            'total_other_files':    None,
                            '--- FA ---':           '--- Folder Average ---',
                            'avg_size_MB':          None,
                            'avg_files':            None,
                            'avg_image_files':      None,
                            'avg_video_files':      None,
                            'avg_other_files':      None,
                            '--- FW ---':           '--- Folder With ---',
                            'FW_max_size_MB':       None,
                            'FW_max_total_files':   None,
                            'FW_max_image_files':   None,
                            'FW_max_video_files':   None,
                            'FW_max_other_files':   None,
                            'FW_max_sMB_per_file':  None
                        }
        
        #[5] Define the DataFrame to store media statistics.
        self.col_df_media_stat = ['Folder Name', 'Size (MB)', 'Total Files',
                                  'Image Files', 'Video Files', 'Other Files']
        self.df_media_stat = pd.DataFrame(columns=self.col_df_media_stat)
        
        #[4] Excel sheet names shared by save and read.
        self.shn1 = '1_metadata'
        self.shn2 = '2_statistics'
        # Note: caller decides what to run next, e.g.
        #   A: scan_media_folders() → calculate_statistics_summary()
        #      → save_stat_result_to_excel() → plot_scan_media_folders()
        #   B: read_stat_result_from_excel(path) → calculate_statistics_summary()
        #      → save_stat_result_to_excel(path, metadata_only=True) → plot_scan_media_folders()



    def _stat_single_date_folder(self, dir_folder, img_exts, video_exts):
        """
        Return (size_bytes, cnt_total, cnt_image, cnt_video, cnt_other) for one date folder.
        Uses scandir for flat folders; falls back to os.walk only when files live in subfolders.
        """
        size_bytes = cnt_total = cnt_image = cnt_video = cnt_other = 0
        cnt_subdirs = 0

        def _tally_file(name, size):
            nonlocal size_bytes, cnt_total, cnt_image, cnt_video, cnt_other
            cnt_total += 1
            size_bytes += size
            ext = os.path.splitext(name)[1].lower()
            if ext in img_exts:
                cnt_image += 1
            elif ext in video_exts:
                cnt_video += 1
            else:
                cnt_other += 1

        # entry.stat() is free on Windows: scandir already carries the size,
        # so no extra per-file syscall (unlike os.path.getsize).
        with os.scandir(dir_folder) as it:
            for entry in it:
                if entry.is_file(follow_symlinks=False):
                    try:
                        size = entry.stat(follow_symlinks=False).st_size
                    except OSError:
                        size = 0
                    _tally_file(entry.name, size)
                elif entry.is_dir(follow_symlinks=False):
                    cnt_subdirs += 1

        # Some date folders store media in subfolders; walk only when needed.
        if cnt_total == 0 and cnt_subdirs > 0:
            for root, _dirs, files in os.walk(dir_folder):
                if root == dir_folder:
                    continue
                for name in files:
                    try:
                        size = os.path.getsize(os.path.join(root, name))
                    except OSError:
                        size = 0
                    _tally_file(name, size)

        return size_bytes, cnt_total, cnt_image, cnt_video, cnt_other


    def scan_media_folders(self):
        """
        Generate df_media_stat that contain the following columns:
        ['Folder Name', 'Size (MB)', 'Total Files', 'Image Files', 'Video Files', 'Other Files']
        
        Note: 
        - Slowdown over thousands of folders is disk metadata I/O, not memory.
        - No gc/dump needed — only tiny row dicts are retained.
        - A long pause usually means one folder (cloud sync, huge file count, or nested media).
        """
        #[1] Stamp when this scan started.
        self.dts_scan = datetime.now().strftime("%Y-%m%d-%H%M")
        self.dict_meta['Scan'] = self.dts_scan
        print(f'\n[scan_media_folders] {self.dts_scan}')
        text_note = 'Note: f/s = folders per second.'
        t_start = time.time()
        
        
        #[3] Prepare sets of image and video extensions for quick lookup.
        img_exts = set(e.lower() for e in M0C.LIST_EXT_IMAGE)
        video_exts = set(e.lower() for e in M0C.LIST_EXT_VIDEO)
        list_rows = []
        list_bsn_sorted = sorted(self.list_bsn_date_folders)
        cnt_folders = len(list_bsn_sorted)
        print_every = 50
        slow_folder_sec = 2.0
        
        #[4] Scan folders in parallel. Metadata I/O releases the GIL, and a
        #    deep request queue lets the disk reorder seeks — this is what
        #    fixes the multi-second stalls on cold (uncached) folders.
        def _scan_one_folder(bsn):
            t_folder = time.time()
            try:
                stats = self._stat_single_date_folder(
                    os.path.join(self.dir_media, bsn), img_exts, video_exts)
            except OSError as e:
                return bsn, None, time.time() - t_folder, e
            return bsn, stats, time.time() - t_folder, None
        
        #[5] executor.map preserves folder order, so progress prints stay sorted.
        #    Keep workers low: on a single HDD more threads only deepen the disk
        #    queue and starve other apps (e.g. File Explorer) without more speed.
        with ThreadPoolExecutor(max_workers=4) as executor:
            for i, (bsn, stats, dt_folder, error) in enumerate(
                    executor.map(_scan_one_folder, list_bsn_sorted)):
                n = i + 1
                
                if error is not None:
                    print(f'-- Skip {bsn}: {error}', flush=True)
                    continue
                
                size_bytes, cnt_total, cnt_image, cnt_video, cnt_other = stats
                size_mb = round(size_bytes / (1024 * 1024), 2)
                list_rows.append({'Folder Name':  bsn,
                                  'Size (MB)':    size_mb,
                                  'Total Files':  cnt_total,
                                  'Image Files':  cnt_image,
                                  'Video Files':  cnt_video,
                                  'Other Files':  cnt_other})
                
                #[6] Print status for slow folders.
                if dt_folder >= slow_folder_sec:
                    print(f'-- [{n:04d}/{cnt_folders:04d}] {bsn} \t| {cnt_total} files \t| {size_mb} MB |'
                          f' \t| {dt_folder:.1f} sec \t| {datetime.now().strftime("%H:%M:%S.%f")[:-2]} | SLOW', flush=True)
                
                if n == 1 or n == cnt_folders or n % print_every == 0:
                    elapsed = time.time() - t_start
                    rate = n / elapsed if elapsed >= 1.0 else 0
                    print(f'-- [{n:04d}/{cnt_folders:04d}] {bsn} \t| {cnt_total} files \t| {size_mb} MB |'
                          f' \t| {rate:.1f} f/s \t| {datetime.now().strftime("%H:%M:%S.%f")[:-2]}', flush=True)
        
        self.df_media_stat = pd.DataFrame(list_rows, columns=self.col_df_media_stat)
        print(f'-- Done {cnt_folders} folders in {(time.time()-t_start)/60:.1f} min.', flush=True)
        
        return self.df_media_stat

    def calculate_statistics_summary(self):
        """
        From df_media_stat (fresh or read from excel), calculate summary statistics
        and store them in dict_meta. Also refreshes date-range fields from the table
        so a replot from Excel matches the data being summarized.
        """
        print(f'\n[calculate_statistics_summary]')
        
        #[1] Stamp when statistics were calculated.
        self.dts_stat = datetime.now().strftime("%Y-%m%d-%H%M")
        self.dict_meta['Statistics'] = self.dts_stat
        
        if self.df_media_stat.empty:
            print('-- df_media_stat is empty. Summary left as None.')
            return self.dict_meta
        
        df = self.df_media_stat.sort_values('Folder Name').reset_index(drop=True)
        n = len(df)
        
        #[2] Date coverage from the table itself (not from a fresh disk listing).
        self.date_start = df['Folder Name'].iloc[0]
        self.date_end   = df['Folder Name'].iloc[-1]
        self.days_covered = (datetime.strptime(self.date_end, '%Y-%m-%d')
                             - datetime.strptime(self.date_start, '%Y-%m-%d')).days + 1
        self.dict_meta['total_date_folders'] = n
        self.dict_meta['date_start']   = self.date_start
        self.dict_meta['date_end']     = self.date_end
        self.dict_meta['days_covered'] = self.days_covered
        
        #[3] Longest gap between consecutive date folders.
        list_dates = [datetime.strptime(d, '%Y-%m-%d') for d in df['Folder Name']]
        longest_gap_days, longest_gap_start = 0, None
        for i in range(1, len(list_dates)):
            gap = (list_dates[i] - list_dates[i - 1]).days - 1   # days with no folder
            if gap > longest_gap_days:
                longest_gap_days = gap
                longest_gap_start = list_dates[i - 1].strftime('%Y-%m-%d')
        self.dict_meta['longest_gap_days']  = longest_gap_days
        self.dict_meta['longest_gap_start'] = longest_gap_start
        
        #[4] Empty folders.
        self.dict_meta['cnt_empty_folders'] = int((df['Total Files'] == 0).sum())
        
        #[5] Media Folder Statistics (totals).
        self.dict_meta['total_size_MB']     = round(float(df['Size (MB)'].sum()), 2)
        self.dict_meta['total_files']       = int(df['Total Files'].sum())
        self.dict_meta['total_image_files'] = int(df['Image Files'].sum())
        self.dict_meta['total_video_files'] = int(df['Video Files'].sum())
        self.dict_meta['total_other_files'] = int(df['Other Files'].sum())
        
        #[6] Folder Average.
        self.dict_meta['avg_size_MB']     = round(float(df['Size (MB)'].mean()), 2)
        self.dict_meta['avg_files']       = round(float(df['Total Files'].mean()), 2)
        self.dict_meta['avg_image_files'] = round(float(df['Image Files'].mean()), 2)
        self.dict_meta['avg_video_files'] = round(float(df['Video Files'].mean()), 2)
        self.dict_meta['avg_other_files'] = round(float(df['Other Files'].mean()), 2)
        
        #[7] Folder With (maxima) — store "folder | value" for readability.
        def _fw_max(col):
            idx = df[col].idxmax()
            return f"{df.loc[idx, 'Folder Name']} | {df.loc[idx, col]}"
        
        self.dict_meta['FW_max_size_MB']     = _fw_max('Size (MB)')
        self.dict_meta['FW_max_total_files'] = _fw_max('Total Files')
        self.dict_meta['FW_max_image_files'] = _fw_max('Image Files')
        self.dict_meta['FW_max_video_files'] = _fw_max('Video Files')
        self.dict_meta['FW_max_other_files'] = _fw_max('Other Files')
        
        #[8] Max size-per-file among folders that have at least one file.
        df_nz = df[df['Total Files'] > 0].copy()
        if df_nz.empty:
            self.dict_meta['FW_max_sMB_per_file'] = None
        else:
            df_nz['sMB_per_file'] = df_nz['Size (MB)'] / df_nz['Total Files']
            idx = df_nz['sMB_per_file'].idxmax()
            self.dict_meta['FW_max_sMB_per_file'] = (
                f"{df_nz.loc[idx, 'Folder Name']} | {round(float(df_nz.loc[idx, 'sMB_per_file']), 2)}"
            )
        
        print(f'-- Summary ready: {self.dict_meta["total_files"]} files, '
              f'{self.dict_meta["total_size_MB"]} MB, '
              f'{n} folders ({self.date_start} ~ {self.date_end}).')
        return self.dict_meta


    def _save_dict_meta_to_excel(self, path_xlsx):
        #[2] Save metadata as a two-column key/value table (no index column).
        #    Matches save_dict_as_excel_overwrite / read_excel_with_two_columns_into_dict.
        M1F.save_dict_as_excel_overwrite(self.dict_meta, path_xlsx, self.shn1)
        M1F.adjust_multiple_column_widths(path_xlsx, self.shn1,
                                          ['A', 'B'], ['22', '80'])

    def save_stat_result_to_excel(self, path_xlsx=None, metadata_only=False):
        """
        Sheet 1 (shn1 = '1_metadata') is the metadata of the statistics.
        Sheet 2 (shn2 = '2_statistics') is the statistics of the media files.
        
        path_xlsx:      if given, write into that file; otherwise create a new one.
        metadata_only:  if True, only regenerate sheet 1 (path B after reading sheet 2).
        """
        print(f'\n[save_stat_result_to_excel]')
        
        #[1] Ensure output directory exists and resolve destination path.
        os.makedirs(self.dir_output, exist_ok=True)
        if path_xlsx is None:
            bsn_xlsx = f'Media Folder Stat_{self.dir_bsn}_{self.dts_stat}.xlsx'
            path_xlsx = os.path.join(self.dir_output, bsn_xlsx)
        
        #[2] Always write / refresh metadata sheet 1.
        self._save_dict_meta_to_excel(path_xlsx)
        
        #[3] Write statistics sheet 2 unless this is a metadata-only refresh.
        if not metadata_only:
            #    A=Folder Name, B=Size (MB), C=Total Files,
            #    D=Image Files, E=Video Files, F=Other Files  (index=False)
            M1F.save_df_as_excel_overwrite(self.df_media_stat, path_xlsx, self.shn2, index=False)
            list_column_letters = ['A', 'B', 'C', 'D', 'E', 'F']
            list_column_widths  = ['14', '12', '12', '12', '12', '12']
            M1F.adjust_multiple_column_widths(path_xlsx, self.shn2, list_column_letters, list_column_widths)
        
        #[4] Open output folder.
        M1F.open_a_folder_on_windows(self.dir_output)
        print(f'-- Media folder statistics saved to: {path_xlsx}'
              f'{" (metadata only)" if metadata_only else ""}')
        return path_xlsx


    def read_stat_result_from_excel(self, path_xlsx):
        """
        Load df_media_stat from sheet shn2 only. Sheet shn1 is intentionally
        not restored — call calculate_statistics_summary() afterwards to build
        a fresh dict_meta, then save_stat_result_to_excel(..., metadata_only=True).
        
        If the old sheet 1 has a 'Scan' stamp, it is preserved so the original
        scan time is not lost when regenerating statistics.
        """
        print(f'\n[read_stat_result_from_excel] {path_xlsx}')
        
        #[1] Validate the path.
        if not path_xlsx or not os.path.isfile(path_xlsx):
            raise FileNotFoundError(f'Excel report not found: {path_xlsx}')
        
        #[2] Prefer Scan from sheet 1; fall back to filename when sheet 1 is
        #    damaged/unreadable or Scan is missing / blank / NaN / "nan".
        #    Filename pattern: Media Folder Stat_{dir_bsn}_{YYYY-MMDD-HHMM}.xlsx
        def _is_usable_scan(val):
            if val is None or val is False:
                return False
            try:
                if pd.isna(val):
                    return False
            except (TypeError, ValueError):
                pass
            s = str(val).strip()
            if s == '' or s.lower() in ('nan', 'none', 'null'):
                return False
            return True
        
        scan_from_sheet = False
        try:
            dict_old = M1F.read_excel_with_two_columns_into_dict(path_xlsx, self.shn1)
            scan_val = dict_old.get('Scan')
            if _is_usable_scan(scan_val):
                self.dts_scan = str(scan_val).strip()
                self.dict_meta['Scan'] = self.dts_scan
                scan_from_sheet = True
                print(f'-- Preserved Scan timestamp from sheet "{self.shn1}": {self.dts_scan}')
            else:
                print(f'-- Sheet "{self.shn1}" readable, but Scan is missing/blank/nan ({scan_val!r}).')
        except Exception as e:
            print(f'-- Sheet "{self.shn1}" damaged or unreadable ({e}).')
        
        #[3] Filename fallback when sheet 1 did not yield a usable Scan value.
        if not scan_from_sheet:
            print(f'\n⚠️[Warning] Sheet "{self.shn1}" did not yield a Scan timestamp.')
            bsn = os.path.basename(path_xlsx)
            match = re.search(r'_(\d{4}-\d{4}-\d{4})\.xlsx$', bsn)
            if match:
                self.dts_scan = match.group(1)
                self.dict_meta['Scan'] = self.dts_scan
                print(f'-- Preserved Scan timestamp from filename: {self.dts_scan}')
            else:
                print(f'-- No Scan stamp in filename either; keeping init value: {self.dts_scan}')
        
        #[4] Read the statistics sheet and validate the expected columns.
        #    (Column A is the saved index and is dropped by the column filter.)
        df = M1F.read_excel_sheet_into_df(path_xlsx, self.shn2)
        list_missing = [c for c in self.col_df_media_stat if c not in df.columns]
        if list_missing:
            raise ValueError(f'Sheet "{self.shn2}" is missing columns {list_missing} in {path_xlsx}.')
        
        self.df_media_stat = df[self.col_df_media_stat].copy()
        # pandas may parse YYYY-MM-DD folder names as datetimes — force strings.
        self.df_media_stat['Folder Name'] = self.df_media_stat['Folder Name'].astype(str).str[:10]
        print(f'-- Loaded {len(self.df_media_stat)} rows from sheet "{self.shn2}".')
        return self.df_media_stat




    def plot_scan_media_folders(self):
        """
        Plot a chart of the media folder statistics.
        - A horizontally oriented line chart.
        - X-axis: Folder Name. Mark the first and last date folders, plus the 1th day of each month.
        - Left 1st Y-axis: Count of Files (Total, Image, Video, Other).
        - Right 2nd Y-axis: Size (MB)
        Style:
        - Total: Circle
        - Image: Square
        - Video: Triangle
        - Other: Short bar
        - Size (MB): Transparent light gray bars.
        """
        import matplotlib
        matplotlib.use('Agg')   # Render to file; no GUI window needed.
        import matplotlib.pyplot as plt
        
        print(f'\n[plot_scan_media_folders]')
        if self.df_media_stat.empty:
            print('-- df_media_stat is empty. Nothing to plot.')
            return None
        
        #[1] Sort by date so the X-axis reads chronologically.
        df = self.df_media_stat.sort_values('Folder Name').reset_index(drop=True)
        x = np.arange(len(df))
        fs_title, fs_axis, fs_tick, fs_legend = 18, 14, 9, 11
        
        #[2] Set up figure with two Y-axes sharing the X-axis.
        fig, ax_cnt = plt.subplots(figsize=(24, 8))
        ax_size = ax_cnt.twinx()
        
        #[3] Right axis: Size (MB) as transparent light gray bars (drawn first, behind lines).
        ax_size.bar(x, df['Size (MB)'], width=1.0, color='darkgray', alpha=0.9,
                    label='Size (MB)', zorder=1)
        ax_size.set_ylabel('Size (MB)', fontsize=fs_axis, color='gray')
        ax_size.tick_params(axis='y', labelcolor='gray', labelsize=fs_tick)
        
        #[4] Left axis: file counts as lines with the specified markers.
        #    Keep lines thin and markers small — with ~3000 folders, bold styles smear.
        ax_cnt.plot(x, df['Total Files'], marker='o', markersize=3, linewidth=0.6,
                    color='tab:blue',   label='Total Files',  zorder=4)
        ax_cnt.plot(x, df['Image Files'], marker='s', markersize=3, linewidth=0.6,
                    color='tab:green',  label='Image Files',  zorder=3)
        ax_cnt.plot(x, df['Video Files'], marker='^', markersize=3, linewidth=0.6,
                    color='tab:red',    label='Video Files',  zorder=3)
        ax_cnt.plot(x, df['Other Files'], marker='_', markersize=6, linestyle='None',
                    color='tab:orange', label='Other Files',  zorder=3)
        ax_cnt.set_ylabel('Count of Files', fontsize=fs_axis)
        ax_cnt.tick_params(axis='y', labelsize=fs_tick)
        ax_cnt.set_xlabel('Date Folder', fontsize=fs_axis)
        
        #[5] Put the line axis above the bar axis so bars stay in the background.
        ax_cnt.set_zorder(ax_size.get_zorder() + 1)
        ax_cnt.patch.set_visible(False)
        
        #[5b] Align the zero of both Y-axes: all values are non-negative, so
        #     pinning both bottoms to 0 puts the two zeros on the same line.
        ax_cnt.set_ylim(bottom=0)
        ax_size.set_ylim(bottom=0)
        
        #[6] X-ticks: first folder, last folder, and every 1st day of a month.
        #    (Month starts missing from the library won't produce a tick.)
        list_names = df['Folder Name'].tolist()
        tick_pos = [i for i, name in enumerate(list_names)
                    if i == 0 or i == len(list_names) - 1 or name.endswith('-01')]
        ax_cnt.set_xticks(tick_pos)
        ax_cnt.set_xticklabels([list_names[i] for i in tick_pos],
                               rotation=90, fontsize=fs_tick)
        ax_cnt.set_xlim(-1, len(list_names))
        ax_cnt.grid(axis='y', linestyle=':', alpha=0.4)
        
        #[7] Combined legend from both axes.
        handles_cnt, labels_cnt = ax_cnt.get_legend_handles_labels()
        handles_size, labels_size = ax_size.get_legend_handles_labels()
        ax_cnt.legend(handles_cnt + handles_size, labels_cnt + labels_size,
                      loc='upper left', fontsize=fs_legend)
        
        ax_cnt.set_title(f'Media Folder Statistics — {self.dir_bsn} ({list_names[0]} ~ {list_names[-1]})',
                         fontsize=fs_title)
        fig.tight_layout()
        
        #[8] Save plot and clean up.
        os.makedirs(self.dir_output, exist_ok=True)
        path_png = os.path.join(self.dir_output, f'Media Folder Stat_{self.dir_bsn}_{self.dts_stat}.png')
        fig.savefig(path_png, dpi=150)
        plt.close(fig)
        
        print(f'-- Media folder statistics plot saved to: {path_png}')
        return path_png







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
        M1F.save_df_as_excel_overwrite(self.df_gps, path_xlsx, sheet_name)

        #[3] Adjust column widths.
        #    (A=index), B=File Name, C=Date Taken, D=Time Taken,
        #    E=Latitude, F=Longitude, G=Location Name, H=Note
        list_column_letters = ['A', 'B', 'C', 'D', 'E',  'F',  'G',  'H']
        list_column_widths  = ['5', '30','14','12','14', '14', '25', '30']
        M1F.adjust_multiple_column_widths(path_xlsx, sheet_name, list_column_letters, list_column_widths)

        #[4] Open output folder.
        M1F.open_a_folder_on_windows(self.dir_output)
        print(f'-- GPS info saved to: {path_xlsx}')
