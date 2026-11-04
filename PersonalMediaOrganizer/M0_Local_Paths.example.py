"""
[M0_Local_Paths.example.py]
Purpose: Template for the machine-specific settings of one user.
         Copy this file to M0_Local_Paths.py (same folder) and fill in your own values.
         M0_Local_Paths.py is gitignored, so your real folders and coordinates are never committed.
Note:
    1. M0_Configuration.py reads M0_Local_Paths.py if it exists.
    2. Everything below is optional except LIST_DIR_MEDIA.
    3. Do not put real paths or coordinates in this example file. It is committed.
"""

#[1] Every media library, e.g. one folder per decade. Scripts use the first as the default,
#    and PMO-21, PMO-22, PMO-32 and the folder GUI read the last or all of them.
LIST_DIR_MEDIA = [
    r'C:\path\to\your\media\library_2011-2020',
    r'C:\path\to\your\media\library_2021-2030',
]

#[2] Optional. Default media folder if it should differ from LIST_DIR_MEDIA[0].
# DIR_MEDIA = r'C:\path\to\your\media\library_2011-2020'

#[3] Optional. Where reports are written. Default is the project's own 06_output folder.
# DIR_OUTPUT = r'C:\path\to\your\reports'

#[4] Optional. Default search center for PMO-22, in decimal degrees (north and east positive).
# LAT_CENTER = 0.000000
# LON_CENTER = 0.000000
