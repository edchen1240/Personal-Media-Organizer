# AGENTS.md

Instructions for coding agents and contributors working on Personal Media Organizer (PMO), a local-first Python toolkit that sorts iPhone photo and video exports into `YYYY-MM-DD` folders. Read `README.md` for what each tool does.

## Layout

- `02_scripts/` holds one runnable script per tool, named `PMO-NN_Title.py`.
- `03_launchers/` holds the matching Windows launcher for each script, named `[B]_PMO-NN_Title.bat`.
- `PersonalMediaOrganizer/` holds the shared modules: `M0_Configuration`, `M1_Files`, `M3_Image`, `M4_Classes`, `M5_Statistics`, `M6_System`, `M8_Folder GUI`.
- `06_output/` receives generated reports. Its files are not committed.

## Rules that must not break

- Never write an absolute local path, a latitude/longitude, or an e-mail address into a tracked file, comment, docstring or commit message. Use `C:\path\to\...` as a placeholder.
- Read folders and coordinates through `PersonalMediaOrganizer/M0_Configuration.py` (`LIST_DIR_MEDIA`, `DIR_OUTPUT`, `LAT_CENTER`, `LON_CENTER`). Those values come from a gitignored `M0_Local_Paths.py`; the committed template is `M0_Local_Paths.example.py`. Do not commit the local file.
- A script that needs a folder asks for it (dialog, argument, or `M0C`). It never hard-codes one.
- Launchers stay portable: resolve the project from `%~dp0..` and fall back to the `PMO_HOME` user variable, as the existing launchers do.
- `PMO-10` and the other organizers move files, they do not copy. Test on a copy of a folder, never on a real library.

## Conventions

- Each script starts with a docstring: `[file name]`, Purpose, Author, Date, Status. Numbered step comments follow the `#[1]`, `#[2]` pattern.
- A new tool gets a script in `02_scripts/`, a launcher in `03_launchers/`, and a row in the README Tools table.
- Keep user-facing behavior claims in the README true to the code. Check the code before changing a claim.

## Checks

There is no test suite. After editing a script, run `python -m py_compile "<script>"`, then run it on a small copy of sample media. Dependencies are in `requirements.txt`; video dates need FFmpeg on your PATH.
