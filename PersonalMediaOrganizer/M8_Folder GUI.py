"""
[MDS_M8_Folder GUI]
Purpose: Provide a fast launch pad for dated media folders.
Author: Meng-Chi Ed Chen
Date: 2024-0613
Notes:
2026-08-18: On date click, warm that day ±3 neighboring date folders then open.
            Ctrl+click copies the path and warms the same window (does not open).
            Enter/Refresh in the focus-date bar does the same warm±3 then open.
            Warming runs on a background thread so the GUI stays responsive; the
            clicked day is warmed first, then Explorer opens, then neighbors warm.

Status: Complete.
"""

import os, sys, ctypes, threading
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from datetime import datetime
import tkinter as tk

from PersonalMediaOrganizer import M1_Files as M1F
from PersonalMediaOrganizer import M6_System as M6S

DIR_MEDIA = r"D:\01_Floor\b_Memory\01_DailyPhotosVedios_2021-2030"
WARM_RADIUS_DAYS = 3


def close_explorer_by_date(date_str, exact=False):
    """Close visible Windows Explorer windows whose title matches the given date string."""
    user32 = ctypes.windll.user32
    WM_CLOSE = 0x0010
    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    GetWindowTextLengthW = user32.GetWindowTextLengthW
    GetWindowTextW = user32.GetWindowTextW
    IsWindowVisible = user32.IsWindowVisible
    PostMessageW = user32.PostMessageW
    targets = []

    @EnumWindowsProc
    def _proc(hwnd, _):
        if IsWindowVisible(hwnd):
            length = GetWindowTextLengthW(hwnd)
            if length > 0:
                buf = ctypes.create_unicode_buffer(length + 1)
                GetWindowTextW(hwnd, buf, length + 1)
                title = buf.value or ""
                if (title == date_str) if exact else (date_str in title):
                    targets.append(hwnd)
        return True

    user32.EnumWindows(_proc, 0)
    for hwnd in targets:
        PostMessageW(hwnd, WM_CLOSE, 0, 0)


def get_list_date_folders(dir_decade, focus_dir_date=None):
    """Return a list of YYYY-MM-DD folders and the index of the focus folder."""
    list_dir_dates = []
    focus_index = None

    #[1] List subdirectories
    list_path_dates = os.listdir(dir_decade)
    for dir_name in sorted(list_path_dates):
        dir_path = os.path.join(dir_decade, dir_name)
        if not os.path.isdir(dir_path):
            continue
        try:
            datetime.strptime(dir_name, "%Y-%m-%d")
        except ValueError:
            continue
        list_dir_dates.append(dir_path)
        
    #[2] Find focus index
    if focus_dir_date:
        for idx, dir_path in enumerate(list_dir_dates):
            if os.path.basename(dir_path) == focus_dir_date:
                focus_index = idx
                break

    return list_dir_dates, focus_index


class MediaFolderOpenerGUI:
    """
    Tkinter GUI for quickly opening dated media folders.
    
    
    """

    def __init__(
        self,
        root,
        dir_decade=DIR_MEDIA,
        focus_dir_date="2024-01-01",
         ):
        
        #[1] Initialize GUI
        self.root = root
        self.root.title('Media Folder Opener')
        self.root.geometry('600x900')

        
        #[3] Initialize instance variables
        self.dir_decade = dir_decade
        self.focus_dir_date = focus_dir_date
        self.list_dir_dates, self.focus_index = get_list_date_folders(
            self.dir_decade, self.focus_dir_date)
        self.current_date = None

        #[5] Initialize pagination variables
        self.num_columns = 3
        self.rows_per_column = 20
        self.page_size = self.num_columns * self.rows_per_column
        self.start_index = self._calc_start_index()

        self.status_var = tk.StringVar(value="Ready")
        self.section_frames = {}
        self.buttons = []
        self.default_button_bg = None
        self._warm_gen = 0

        self.initiate_GUI_structure()

    def initiate_GUI_structure(self):
        """Build the top controls and button grid."""
        self.section_I()
        self.section_II()
        self.update_button_grid()

    def section_I(self):
        """
        From left to right:
        - Entry box for focus date (YYYY-MM-DD)
        - Refresh button
        - Left scroll button
        - Right scroll button
        - Status label
        Eveything in this section should be horizontally centered.
        """
        frame = tk.Frame(self.root)
        frame.pack(fill=tk.X, padx=10, pady=10)
        self.section_frames["top"] = frame
        controls = tk.Frame(frame)
        controls.pack(anchor="center")
        entry = tk.Entry(controls, width=40)
        entry.insert(0, self.focus_dir_date)
        entry.grid(row=0, column=0, padx=5)
        entry.bind("<Return>", lambda _: self.refresh_focus_date())
        self.focus_entry = entry

        refresh_btn = tk.Button(controls, text="Refresh", command=self.refresh_focus_date)
        refresh_btn.grid(row=0, column=1, padx=5)

        left_btn = tk.Button(controls, text="<", width=3, command=self.scroll_left)
        left_btn.grid(row=0, column=2, padx=5)

        right_btn = tk.Button(controls, text=">", width=3, command=self.scroll_right)
        right_btn.grid(row=0, column=3, padx=5)

        status_label = tk.Label(frame, textvariable=self.status_var, anchor="center")
        status_label.pack(pady=(8, 0))

    def section_II(self):
        """
        Three columns of buttons to open date folders.
        The first date folder is on the top-left, and the goes down column-wise.
        """
        frame = tk.Frame(self.root)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.section_frames["buttons"] = frame

        for col in range(self.num_columns):
            frame.grid_columnconfigure(col, weight=1)
            for row in range(self.rows_per_column):
                btn = tk.Button(frame, text="", width=22, command=lambda idx=0: None)
                btn.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
                self.buttons.append(btn)

        if self.buttons:
            self.default_button_bg = self.buttons[0].cget('bg')

    def refresh_focus_date(self):
        """Jump to the typed date, warm ±3 neighbors, and open that folder."""
        focus_value = self.focus_entry.get().strip()
        self.focus_dir_date = focus_value if focus_value else None
        self.list_dir_dates, self.focus_index = get_list_date_folders(
            self.dir_decade, self.focus_dir_date
        )

        if not self.list_dir_dates:
            self.status_var.set('No date folders found.')
            self.start_index = 0
            self.update_button_grid()
            return

        if self.focus_index is None:
            self.status_var.set('Focus date not found; showing earliest folders.')
            self.start_index = self._calc_start_index()
            self.update_button_grid()
            return

        self.start_index = self._calc_start_index()
        self.update_button_grid()
        # Same path as a date-button click: warm ±3 then open Explorer
        self.date_btn_click(self.list_dir_dates[self.focus_index])

    def scroll_left(self):
        if self.start_index == 0:
            self.status_var.set('Already at the beginning.')
            return

        self.start_index = max(0, self.start_index - self.page_size)
        self.status_var.set('Scrolled left.')
        self.update_button_grid()

    def scroll_right(self):
        if not self.list_dir_dates:
            self.status_var.set('No folders to show.')
            return

        max_start = max(0, len(self.list_dir_dates) - self.page_size)
        if self.start_index >= max_start:
            self.status_var.set('Already at the end.')
            return

        self.start_index = min(max_start, self.start_index + self.page_size)
        self.status_var.set('Scrolled right.')
        self.update_button_grid()

    def update_button_grid(self):
        if not self.buttons:
            return

        end_index = self.start_index + self.page_size
        current_slice = self.list_dir_dates[self.start_index:end_index]

        #[6] Update buttons
        for idx, btn in enumerate(self.buttons):
            btn.unbind('<ButtonRelease-1>')
            btn.unbind('<Control-Button-1>')
            if idx < len(current_slice):
                dir_path = current_slice[idx]
                dir_name = os.path.basename(dir_path)
                btn.configure(
                    text=dir_name,
                    state=tk.NORMAL,
                    command=lambda: None,
                )
                btn.bind(
                    '<ButtonRelease-1>',
                    lambda e, p=dir_path: self._on_date_btn_release(e, p),
                )
                if self.default_button_bg is not None:
                    btn.configure(bg=self.default_button_bg)

                global_index = self.start_index + idx
                if self.focus_index is not None and global_index == self.focus_index:
                    btn.configure(bg="#d0e8ff")
            else:
                btn.configure(text="", state=tk.DISABLED, command=lambda: None)
                if self.default_button_bg is not None:
                    btn.configure(bg=self.default_button_bg)

    def _index_of_date_folder(self, path):
        """Return index of path in list_dir_dates, or None."""
        target = os.path.normpath(path)
        for i, dir_path in enumerate(self.list_dir_dates):
            if os.path.normpath(dir_path) == target:
                return i
        return None

    def _dirs_around(self, path, radius=WARM_RADIUS_DAYS):
        """Return [center, …neighbors] for warming: center first, then ±radius."""
        path = os.path.normpath(path)
        center = self._index_of_date_folder(path)
        if center is None:
            return [path]
        lo = max(0, center - radius)
        hi = min(len(self.list_dir_dates), center + radius + 1)
        window = self.list_dir_dates[lo:hi]
        neighbors = [d for d in window if os.path.normpath(d) != path]
        return [path] + neighbors

    def _set_status_async(self, message):
        """Thread-safe status update onto the Tk main loop."""
        self.root.after(0, lambda m=message: self.status_var.set(m))

    def _start_warm_job(self, path, open_after=False, copied=False):
        """
        Warm on a background thread so the window stays responsive.
        Center day is warmed first; if open_after, Explorer opens then;
        neighbors continue warming afterward. A newer click cancels older jobs.
        """
        path = os.path.normpath(path)
        dirs = self._dirs_around(path)
        first = os.path.basename(dirs[0])
        last = os.path.basename(dirs[-1])
        self._warm_gen += 1
        gen = self._warm_gen
        self.status_var.set(f'Warming {len(dirs)} folders ({first} … {last})…')
        thread = threading.Thread(
            target=self._warm_worker,
            args=(path, dirs, open_after, copied, gen),
            daemon=True,
        )
        thread.start()

    def _warm_worker(self, path, dirs, open_after, copied, gen):
        opened = False
        for dir_path in dirs:
            if gen != self._warm_gen:
                return
            M6S.warm_folder_metadata(dir_path, print_every=500)
            if open_after and not opened and os.path.normpath(dir_path) == path:
                opened = True
                self.root.after(0, lambda p=path, g=gen: self._open_folder_ui(p, g))

        if gen != self._warm_gen:
            return
        if copied and not open_after:
            self._set_status_async(f'Copied + warmed: {path}')
        elif open_after:
            self._set_status_async(
                f'Opened {os.path.basename(path)} (warmed ±{WARM_RADIUS_DAYS})'
            )
        else:
            self._set_status_async(f'Warmed ±{WARM_RADIUS_DAYS} around {os.path.basename(path)}')

    def _open_folder_ui(self, path, gen):
        """Open Explorer on the Tk thread after the center day is warm."""
        if gen != self._warm_gen:
            return
        try:
            M1F.open_a_folder_on_windows(path)
            self.status_var.set(
                f'Opened {os.path.basename(path)}; still warming neighbors…'
            )
        except Exception as exc:
            self.status_var.set(f'Failed to open folder: {exc}')

    def _on_date_btn_release(self, event, path):
        """Plain click opens; Ctrl+click copies path. Both warm ±3 days."""
        if event.state & 0x0004:
            return self._ctrl_click_copy_and_warm(event, path)
        self.date_btn_click(path)

    def _ctrl_click_copy_and_warm(self, event, path):
        """Ctrl+click: copy path immediately; warm ±3 days in the background."""
        path = os.path.normpath(path)
        self.root.clipboard_clear()
        self.root.clipboard_append(path)
        self.root.update_idletasks()
        self._start_warm_job(path, open_after=False, copied=True)
        return 'break'

    def date_btn_click(self, path):
        """
        1. Close any previously opened folder windows for self.current_date.
        2. Update self.current_date.
        3. Warm selected day (then open) and ±3 neighbors on a background thread.
        """
        path = os.path.normpath(path)

        #[1] Close the self.current_date folders.
        if self.current_date:
            close_explorer_by_date(self.current_date, exact=False)

        #[2] Update current date
        self.current_date = os.path.basename(path)

        #[3] Warm center → open Explorer → warm neighbors (non-blocking UI)
        self._start_warm_job(path, open_after=True, copied=False)

    def _calc_start_index(self):
        """
        The focus_date should be at the top of the second column if possible.
        """

        if self.focus_index is None:
            return 0

        max_start = max(0, len(self.list_dir_dates) - self.page_size)
        preferred_start = max(0, self.focus_index - 1)
        return min(preferred_start, max_start)

if __name__ == "__main__":
    root = tk.Tk()
    app = MediaFolderOpenerGUI(root)
    root.mainloop()

























