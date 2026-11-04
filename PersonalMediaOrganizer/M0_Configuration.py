"""
[M0_Configuration.py]
Purpose: Set up directory for user.
Author: Meng-Chi Ed Chen
Date: 2026-07-05

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



#[1] User relative path to find the root directory of this project. 
DIR_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#[2] Where this user stores media files. 
#    Machine-specific paths live in M0_Local_Paths.py, which is gitignored and never committed.
#    Copy M0_Local_Paths.example.py to M0_Local_Paths.py and fill in your own folders.
#    Without it, PMO_MEDIA_DIR (environment variable) is used; without that, a placeholder is used and a warning is printed.
try:
    from PersonalMediaOrganizer import M0_Local_Paths as _LP
except ImportError:
    _LP = None

#[3] Media libraries. LIST_DIR_MEDIA holds every library (e.g. one per decade); DIR_MEDIA is the default one.
LIST_DIR_MEDIA = list(getattr(_LP, 'LIST_DIR_MEDIA', []))
if not LIST_DIR_MEDIA:
    _env_media = os.environ.get('PMO_MEDIA_DIR')
    LIST_DIR_MEDIA = [_env_media] if _env_media else [r'C:\path\to\your\media\library']
    if not _env_media:
        print('⚠️ M0_Local_Paths.py not found. Copy PersonalMediaOrganizer/M0_Local_Paths.example.py to M0_Local_Paths.py '
              'and set LIST_DIR_MEDIA, or set the PMO_MEDIA_DIR environment variable.')
DIR_MEDIA = getattr(_LP, 'DIR_MEDIA', LIST_DIR_MEDIA[0])

#[4] Default output directory for reports.
DIR_OUTPUT = getattr(_LP, 'DIR_OUTPUT', os.path.join(DIR_ROOT, '06_output'))

#[4.5] Optional default search center for PMO-22 (decimal degrees). None means the --lat and --lon flags are required.
LAT_CENTER = getattr(_LP, 'LAT_CENTER', None)
LON_CENTER = getattr(_LP, 'LON_CENTER', None)











#[5] Miscellaneous settings
LIST_EXT_IMAGE = ['.jpg', '.jpeg', '.png', '.heic', '.tiff', '.bmp']
LIST_EXT_VIDEO = ['.mp4', '.mov', '.avi', '.mkv', '.wmv']


