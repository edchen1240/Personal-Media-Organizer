"""
[PMO-22_Search photos by date range and GPS radius.py]
Purpose: List JPG photos whose date folder falls in a time range and whose GPS
         falls inside a radius. The photos stay where they are.
Author: Meng-Chi Ed Chen
Date: 2026-10-20
Note:
    1. The time filter is the YYYY-MM-DD folder name, the same cut PMO-21 uses.
       EXIF capture time is written on the sheet and does not include or exclude a photo.
    2. The start and end dates snap to the nearest existing date folder within 3 days.
       A date with no folder in that window stops the run.
    3. Only .jpg and .jpeg are opened. A photo with no GPS, or a photo outside the
       radius, is counted and left off the sheet.
    4. Pass --lat, --lon, and --radius-m to override the constants.
       With no override the center is LAT_CENTER and LON_CENTER from the gitignored
       PersonalMediaOrganizer/M0_Local_Paths.py, and the radius is 500 m.
       Without that file, --lat and --lon are required.
    5. Distance is the great-circle length on a 6371000 m sphere.
       A photo exactly on the radius is a match.
    6. The default range is 2020-01-01 through 2021-12-31.
       It crosses the two decade libraries, so a run with no --dir-media reads both.
    7. Each workbook name ends in _ddHHmm, the day and minute the file was written,
       so a later run does not overwrite an earlier one.
    8. File Name is a link to the photo. Clicking it opens the file.
    9. Weekday sits beside Date Folder. 1 is Monday and 7 is Sunday.
Status: Working.

Usage:
    python "PMO-22_Search photos by date range and GPS radius.py" --date-start 2019-06-01 --date-end 2019-06-30
    python "PMO-22_Search photos by date range and GPS radius.py" --date-start 2019-06-01 --date-end 2019-06-30 --lat 25.0 --lon 121.5 --radius-m 500
    python "PMO-22_Search photos by date range and GPS radius.py" --dir-media "C:/path/to/media/library" --date-start 2019-06-01 --date-end 2019-06-30

Agent guidance:
    Omit the date flags to use 2020-01-01 through 2021-12-31.
    Omit --lat, --lon, and --radius-m to use LAT_CENTER, LON_CENTER from M0_Local_Paths.py, and 500 m.
    The script writes one xlsx under 06_output and does not copy or move photos.
    Read the summary counts before treating an empty sheet as a failed run.

Example:
    python "PMO-22_Search photos by date range and GPS radius.py" --date-start 2019-06-01 --date-end 2019-06-30 --radius-m 500
"""

import argparse, math, os, re, sys
from datetime import datetime, timedelta
from pathlib import Path

import exifread
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Font


#[1] Constants and paths. Machine-specific values come from the gitignored M0_Local_Paths.py via M0_Configuration.
DIR_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, DIR_ROOT)
from PersonalMediaOrganizer import M0_Configuration as M0C
LIST_DIR_MEDIA = list(M0C.LIST_DIR_MEDIA)
DIR_OUTPUT = M0C.DIR_OUTPUT

#[2] Search defaults.
DATE_START = '2020-01-01'
DATE_END = '2021-12-31'
LAT_CENTER = M0C.LAT_CENTER
LON_CENTER = M0C.LON_CENTER
RADIUS_M = 500.0
CNT_DATE_SEARCH = 3
LIST_EXT = ['.jpg', '.jpeg']
SHEET_NAME = 'GPS Radius'


#[3] Setting descriptions.
"""
[Parameters]
LIST_DIR_MEDIA   Decade libraries read together. CLI --dir-media replaces them with one folder.
DATE_START       First day, YYYY-MM-DD. CLI --date-start replaces it.
DATE_END         Last day, YYYY-MM-DD. CLI --date-end replaces it.
LAT_CENTER       Center latitude, north positive. CLI --lat replaces it.
LON_CENTER       Center longitude, east positive. CLI --lon replaces it.
RADIUS_M         Radius in meters. CLI --radius-m replaces it.
CNT_DATE_SEARCH  How many days the start or end may snap to find a real folder.
"""


def parse_args(argv):
    """
    Read optional overrides. Omitted flags stay None so the constants remain in force.
    """
    #[1] Flags only. A positional folder would collide with the way this script is launched.
    parser = argparse.ArgumentParser(
        description='List JPG photos in a date-folder range and a GPS radius.')
    parser.add_argument('--dir-media', default=None)
    parser.add_argument('--dir-output', default=None)
    parser.add_argument('--date-start', default=None)
    parser.add_argument('--date-end', default=None)
    parser.add_argument('--lat', type=float, default=None)
    parser.add_argument('--lon', type=float, default=None)
    parser.add_argument('--radius-m', type=float, default=None)
    return parser.parse_args(argv)


def require_date(text, flag_name):
    """
    Accept one YYYY-MM-DD string, or stop when the date was never set.
    """
    #[1] Empty means neither the constant nor the flag was provided.
    if text is None or str(text).strip() == '':
        print(f'❌ {flag_name} is required. Set the constant or pass the flag. Example: 2019-06-01')
        sys.exit(1)

    #[2] Reject a string that is not a calendar day.
    try:
        datetime.strptime(str(text).strip(), '%Y-%m-%d')
    except ValueError:
        print(f'❌ {flag_name} must be YYYY-MM-DD. Got: {text}')
        sys.exit(1)
    return str(text).strip()


def resolve_settings(args):
    """
    Build the run settings. A passed flag replaces the matching constant.
    """
    #[1] Paths and dates. One --dir-media flag searches that folder alone.
    if args.dir_media is not None:
        list_media = [args.dir_media]
    else:
        list_media = list(LIST_DIR_MEDIA)
    dir_output = args.dir_output if args.dir_output is not None else DIR_OUTPUT
    date_start = require_date(
        args.date_start if args.date_start is not None else DATE_START, '--date-start')
    date_end = require_date(
        args.date_end if args.date_end is not None else DATE_END, '--date-end')

    #[2] Center and radius. Zero is a real latitude, so None is the only missing value.
    lat = LAT_CENTER if args.lat is None else args.lat
    lon = LON_CENTER if args.lon is None else args.lon
    radius_m = RADIUS_M if args.radius_m is None else args.radius_m
    if lat is None or lon is None:
        print('❌ No search center. Pass --lat and --lon, or set LAT_CENTER and LON_CENTER in PersonalMediaOrganizer/M0_Local_Paths.py.')
        sys.exit(1)

    #[3] Reject a radius that cannot contain a point.
    if radius_m <= 0:
        print(f'❌ --radius-m must be greater than 0. Got: {radius_m}')
        sys.exit(1)
    for dir_media in list_media:
        if not os.path.isdir(dir_media):
            print(f'❌ Media folder not found: {dir_media}')
            sys.exit(1)
    if date_start > date_end:
        print(f'❌ --date-start {date_start} is after --date-end {date_end}.')
        sys.exit(1)

    return {
        'dir_media': list_media,
        'dir_output': dir_output,
        'date_start': date_start,
        'date_end': date_end,
        'lat': lat,
        'lon': lon,
        'radius_m': radius_m,
    }


def media_roots(dir_media):
    """
    Normalize one media folder or a list of them into a list.
    """
    #[1] The default run passes both decade libraries. A flag passes one path.
    if isinstance(dir_media, (list, tuple)):
        return list(dir_media)
    return [dir_media]


def find_nearest_date_folder(dir_media, target_date_str):
    """
    Return the closest YYYY-MM-DD folder within CNT_DATE_SEARCH days.
    """
    #[1] Walk outward from the requested day, same calendar day first.
    #    A day may live in either decade library.
    list_root = media_roots(dir_media)
    target = datetime.strptime(target_date_str, '%Y-%m-%d')
    for delta in range(CNT_DATE_SEARCH + 1):
        offsets = [0] if delta == 0 else [delta, -delta]
        for offset in offsets:
            folder = (target + timedelta(days=offset)).strftime('%Y-%m-%d')
            for root in list_root:
                if os.path.isdir(os.path.join(root, folder)):
                    return folder

    #[2] Nothing close enough.
    raise FileNotFoundError(
        f'No date folder within {CNT_DATE_SEARCH} days of {target_date_str} in {list_root}.')


def collect_jpg_paths(dir_media, date_start, date_end):
    """
    Gather JPG paths from date folders inside the resolved inclusive range.
    """
    #[1] Date folders only, one level down, names that are exactly YYYY-MM-DD.
    set_folder = set()
    list_path = []
    for root in media_roots(dir_media):
        for name in os.listdir(root):
            if not re.match(r'^\d{4}-\d{2}-\d{2}$', name):
                continue
            if not (date_start <= name <= date_end):
                continue
            dir_folder = os.path.join(root, name)
            if not os.path.isdir(dir_folder):
                continue
            set_folder.add(name)

            #[2] Files sitting in each date folder. Subfolders are not walked.
            for filename in os.listdir(dir_folder):
                if not filename.lower().endswith(tuple(LIST_EXT)):
                    continue
                path = os.path.join(dir_folder, filename)
                if os.path.isfile(path):
                    list_path.append(path)
    return sorted(set_folder), list_path


def tag_text(tag):
    """
    Turn an exifread tag into the text its value prints as.
    """
    #[1] Missing tag.
    if tag is None:
        return ''

    #[2] ASCII GPS refs arrive as str or bytes. Other tags use their printed form.
    values = getattr(tag, 'values', None)
    if isinstance(values, str):
        return values.replace('\x00', '').strip()
    if isinstance(values, bytes):
        return values.decode('ascii', errors='replace').replace('\x00', '').strip()
    return str(tag).replace('\x00', '').strip()


def dms_to_degrees(dms_tag, ref_text):
    """
    Convert an EXIF degrees-minutes-seconds tag to signed decimal degrees.
    """
    #[1] Three rational components: degrees, minutes, seconds.
    degrees = 0.0
    for ratio, scale in zip(dms_tag.values, (1.0, 60.0, 3600.0)):
        if isinstance(ratio, tuple):
            num, den = ratio
        else:
            num, den = ratio.num, ratio.den
        degrees += (float(num) / float(den)) / scale

    #[2] South and west are negative.
    if ref_text in ('S', 'W'):
        degrees = -degrees
    return degrees


def read_capture(path_img):
    """
    Read GPS and the capture clock from one JPG. Missing GPS returns None coordinates.
    """
    #[1] One EXIF pass. details=False skips the thumbnail, which this search does not use.
    with open(path_img, 'rb') as file_img:
        tags = exifread.process_file(file_img, details=False)

    #[2] Capture clock is recorded for the sheet. It is not the time filter.
    clock = tag_text(tags.get('EXIF DateTimeOriginal'))
    if len(clock) >= 19 and clock[4] == ':' and clock[10] == ' ':
        date_taken = clock[:10].replace(':', '-')
        time_taken = clock[11:19]
    else:
        date_taken, time_taken = '', ''

    #[3] GPS. A missing ref is not guessed, so the photo is treated as having no coordinates.
    lat_tag = tags.get('GPS GPSLatitude')
    lon_tag = tags.get('GPS GPSLongitude')
    lat_ref = tag_text(tags.get('GPS GPSLatitudeRef'))
    lon_ref = tag_text(tags.get('GPS GPSLongitudeRef'))
    if lat_tag is None or lon_tag is None or lat_ref not in ('N', 'S') or lon_ref not in ('E', 'W'):
        return None, None, date_taken, time_taken

    lat = dms_to_degrees(lat_tag, lat_ref)
    lon = dms_to_degrees(lon_tag, lon_ref)
    return lat, lon, date_taken, time_taken


def haversine_m(lat1, lon1, lat2, lon2):
    """
    Great-circle distance in meters between two WGS84 points.
    """
    #[1] Mean Earth radius, meters.
    radius = 6371000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lam = math.radians(lon2 - lon1)
    a = (math.sin(d_phi / 2.0) ** 2
         + math.cos(phi1) * math.cos(phi2) * math.sin(d_lam / 2.0) ** 2)
    return 2.0 * radius * math.asin(math.sqrt(a))


def search_radius(list_path, lat0, lon0, radius_m):
    """
    Keep photos inside the radius and count the ones that drop out.
    """
    #[1] Accumulators.
    list_row = []
    cnt_no_gps = 0
    cnt_outside = 0
    cnt_unreadable = 0
    cnt_total = len(list_path)

    #[2] One file at a time. A heartbeat every 250 files shows the scan is moving.
    for i, path_img in enumerate(list_path, start=1):
        folder = os.path.basename(os.path.dirname(path_img))
        name = os.path.basename(path_img)
        try:
            lat, lon, date_taken, time_taken = read_capture(path_img)
        except Exception as exc:
            cnt_unreadable += 1
            print(f'⚠️ unreadable  {name}  {exc}')
            continue

        if lat is None or lon is None:
            cnt_no_gps += 1
        else:
            distance_m = haversine_m(lat0, lon0, lat, lon)
            if distance_m <= radius_m:
                list_row.append({
                    'File Name': name,
                    'Path': path_img,
                    'Date Folder': folder,
                    'Weekday': datetime.strptime(folder, '%Y-%m-%d').isoweekday(),
                    'Date Taken': date_taken,
                    'Time Taken': time_taken,
                    'Latitude': round(lat, 6),
                    'Longitude': round(lon, 6),
                    'Distance m': round(distance_m, 1),
                })
                print(f'✅ {distance_m:8.1f} m  {folder}  {name}')
            else:
                cnt_outside += 1

        if i % 250 == 0 or i == cnt_total:
            print(f'-- [{i:04d}/{cnt_total:04d}] scanned')

    #[3] Closest photos first.
    list_row.sort(key=lambda row: (row['Distance m'], row['Path']))
    counts = {
        'scanned': cnt_total,
        'matched': len(list_row),
        'no_gps': cnt_no_gps,
        'outside': cnt_outside,
        'unreadable': cnt_unreadable,
    }
    return list_row, counts


def save_match_excel(list_row, path_xlsx):
    """
    Write the match sheet, link each file name to its photo, and set column widths.
    A locked file stops the run.
    """
    #[1] Header row even when nothing matched, so the search still leaves a file.
    columns = ['File Name', 'Path', 'Date Folder', 'Weekday', 'Date Taken', 'Time Taken',
               'Latitude', 'Longitude', 'Distance m']
    df = pd.DataFrame(list_row, columns=columns)
    os.makedirs(os.path.dirname(path_xlsx), exist_ok=True)

    #[2] Overwrite this sheet. Other sheets in an existing workbook stay.
    try:
        if os.path.exists(path_xlsx):
            with pd.ExcelWriter(path_xlsx, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                df.to_excel(writer, sheet_name=SHEET_NAME, index=False)
        else:
            with pd.ExcelWriter(path_xlsx, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name=SHEET_NAME, index=False)
    except PermissionError:
        print(f'❌ Cannot write {path_xlsx}. Close the workbook and run again.')
        sys.exit(1)

    #[3] Widths follow the column order above.
    workbook = load_workbook(path_xlsx)
    worksheet = workbook[SHEET_NAME]
    for letter, width in zip(list('ABCDEFGHI'), (28, 80, 14, 12, 14, 12, 14, 14, 12)):
        worksheet.column_dimensions[letter].width = width

    #[4] File Name opens the photo. Path stays plain text so it can be copied.
    link_font = Font(color='0563C1', underline='single')
    for row_i in range(2, worksheet.max_row + 1):
        path_value = worksheet.cell(row=row_i, column=2).value
        if not path_value:
            continue
        name_cell = worksheet.cell(row=row_i, column=1)
        name_cell.hyperlink = Path(str(path_value)).as_uri()
        name_cell.font = link_font
    workbook.save(path_xlsx)
    return path_xlsx


def output_path(settings):
    """
    Name the workbook from the resolved range, center, and radius.
    """
    #[1] Dots in the coordinates stay, so the filename can be read back as numbers.
    #    _ddHHmm is the day and clock minute, so the next run keeps the previous file.
    lat = f'{settings["lat"]:.6f}'
    lon = f'{settings["lon"]:.6f}'
    radius = f'{settings["radius_m"]:g}'
    stamp = datetime.now().strftime('%d%H%M')
    name = (f'GPS Radius_{settings["date_start"]}~{settings["date_end"]}'
            f'_{lat}_{lon}_{radius}m_{stamp}.xlsx')
    return os.path.join(settings['dir_output'], name)


def prepare_console():
    """
    Keep a non-UTF-8 console from crashing on the status marks.
    """
    #[1] Replace unencodable marks instead of raising.
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, 'reconfigure', None)
        if reconfigure is None:
            continue
        try:
            reconfigure(errors='replace')
        except (OSError, ValueError):
            pass


def main(argv):
    """
    Resolve the range, scan the date folders, and write the Excel list.
    """
    #[1] Settings.
    prepare_console()
    print('(•̀ᴗ•́)و  Starting.')
    settings = resolve_settings(parse_args(argv))
    try:
        folder_start = find_nearest_date_folder(settings['dir_media'], settings['date_start'])
        folder_end = find_nearest_date_folder(settings['dir_media'], settings['date_end'])
    except FileNotFoundError as exc:
        print(f'❌ {exc}')
        sys.exit(1)

    #[2] Say when a requested day snapped to a neighboring folder.
    if folder_start != settings['date_start']:
        print(f'☑️ date start snapped from {settings["date_start"]} to {folder_start}, '
              f'nearest folder within {CNT_DATE_SEARCH} days.')
    if folder_end != settings['date_end']:
        print(f'☑️ date end snapped from {settings["date_end"]} to {folder_end}, '
              f'nearest folder within {CNT_DATE_SEARCH} days.')
    if folder_start > folder_end:
        print(f'❌ Resolved range {folder_start} through {folder_end} is empty.')
        sys.exit(1)

    #[3] Scan and write.
    list_folder, list_path = collect_jpg_paths(settings['dir_media'], folder_start, folder_end)
    print(f'-- {folder_start} through {folder_end}, {len(list_folder)} date folders, '
          f'{len(list_path)} JPG, center {settings["lat"]}, {settings["lon"]}, '
          f'radius {settings["radius_m"]:g} m.')
    if not list_path:
        path_xlsx = save_match_excel([], output_path(settings))
        print(f'☑️ 0 JPG files in {folder_start} through {folder_end}. The sheet has headers only.')
        print(f'✅ Excel: {path_xlsx}')
        os.startfile(settings['dir_output'])
        return

    list_row, counts = search_radius(
        list_path, settings['lat'], settings['lon'], settings['radius_m'])
    path_xlsx = save_match_excel(list_row, output_path(settings))
    print(f'-- scanned {counts["scanned"]}, matched {counts["matched"]}, '
          f'no GPS {counts["no_gps"]}, outside {counts["outside"]}, '
          f'unreadable {counts["unreadable"]}')

    #[4] Zero matches is a finished search. The sheet still exists, with headers only.
    if counts['matched'] == 0:
        print(f'☑️ 0 photos inside {settings["radius_m"]:g} m. The sheet has headers only.')
    else:
        print(f'✅ {counts["matched"]} photos inside {settings["radius_m"]:g} m.')
    print(f'✅ Excel: {path_xlsx}')
    os.startfile(settings['dir_output'])


if __name__ == '__main__':
    main(sys.argv[1:])
