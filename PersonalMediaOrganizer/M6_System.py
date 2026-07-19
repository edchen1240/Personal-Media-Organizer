"""
[M6_System.py]
Purpose: System-level helpers — Windows background priority and disk cache
         warming. Used by PMO-29 (current folder) and PMO-30 (media folder).
Author: Meng-Chi Ed Chen
Date: 2026-07-16

How cache warming works:
    1. enter_background_mode() puts the process in Windows "background mode"
       (lowest I/O priority), so it never starves File Explorer or other
       programs — it only uses idle disk time.
    2. warm_folder_metadata() walks every folder single-threaded and stats
       every file. This pulls the NTFS metadata (names, sizes) into RAM cache.
    3. Afterwards, any metadata scan of the same tree reads from RAM instead
       of the disk and completes in seconds.

Status: Complete.
"""
import os, sys, time, ctypes, datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PersonalMediaOrganizer import M0_Configuration as M0C


def enter_background_mode():
    """Lower this process to background CPU/IO priority (Windows only)."""
    PROCESS_MODE_BACKGROUND_BEGIN = 0x00100000
    try:
        handle = ctypes.windll.kernel32.GetCurrentProcess()
        ok = ctypes.windll.kernel32.SetPriorityClass(handle, PROCESS_MODE_BACKGROUND_BEGIN)
        print(f'-- Background I/O priority: {"enabled" if ok else "not available (continuing at normal priority)"}')
    except Exception as e:
        print(f'-- Could not set background priority ({e}). Continuing at normal priority.')


def warm_folder_metadata(dir_media, print_every=200):
    """Touch every file's metadata once so Windows caches it in RAM."""
    print(f'\n[warm_folder_metadata] {dir_media}')
    t_start = time.time()
    cnt_folder = 0
    cnt_file = 0

    for root, _dirs, _files in os.walk(dir_media):
        cnt_folder += 1
        try:
            with os.scandir(root) as it:
                for entry in it:
                    if entry.is_file(follow_symlinks=False):
                        cnt_file += 1
                        try:
                            entry.stat(follow_symlinks=False)
                        except OSError:
                            pass
        except OSError as e:
            print(f'-- Skip {root}: {e}')
            continue

        if cnt_folder % print_every == 0:
            elapsed = time.time() - t_start
            print(f'-- {cnt_folder} folders, {cnt_file} files touched'
                  f' \t| {elapsed:.4f} sec \t| {datetime.datetime.now().strftime("%H:%M:%S.%f")[:-4]}', flush=True)

    elapsed = time.time() - t_start
    print(f'-- Done: {cnt_folder} folders, {cnt_file} files in {elapsed/60:.1f} min.')






