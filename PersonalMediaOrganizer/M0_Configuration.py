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

#[2] Main directory that user store media files. 
DIR_MEDIA = r'D:\01_Floor\b_Memory\01_DailyPhotosVedios_2011-2020'     # The first decade.
# DIR_MEDIA = r'D:\01_Floor\b_Memory\01_DailyPhotosVedios_2021-2030'    # The second dacade.

#[3] Default output directory for reports.
DIR_OUTPUT = os.path.join(DIR_ROOT, '06_output')











#[5] Miscellaneous settings
LIST_EXT_IMAGE = ['.jpg', '.jpeg', '.png', '.heic', '.tiff', '.bmp']
LIST_EXT_VIDEO = ['.mp4', '.mov', '.avi', '.mkv', '.wmv']


