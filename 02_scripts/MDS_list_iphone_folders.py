"""
MDS_list_iphone_folders.py

Enumerate a connected Apple iPhone (on Windows) and list photo folder names and file counts.

How it works
- Uses Windows Shell COM via pywin32 (win32com.client.Dispatch("Shell.Application")).
- Looks under 'This PC' (drives namespace) for an item whose name contains 'iphone'.
- Walks the device tree one level and lists folder names and how many non-folder items they contain.

Limitations / prereqs
- Windows only (relies on Windows Portable Device interface exposed by Explorer).
- Requires pywin32 (install with: python -m pip install pywin32).
- The iPhone must be unlocked and "Trust" accepted. If the driver hasn't initialised, open the device in Explorer once.

This is a lightweight script for quick folder-name + count. For robust cross-platform access consider `libimobiledevice` or iTunes backup APIs.
"""

from __future__ import annotations
import sys
from typing import List, Tuple

try:
    import win32com.client
except Exception:  # ImportError or others
    print("pywin32 is required. Install with: python -m pip install pywin32")
    sys.exit(2)


def get_my_computer_namespace(shell) -> object:
    """Return the 'This PC' / drives namespace (CSIDL_DRIVES = 17)."""
    return shell.Namespace(17)


def find_device_item(namespace, name_substring: str = "iphone") -> object | None:
    """Find a device item under 'This PC' whose name contains name_substring (case-insensitive).

    Returns the COM item or None.
    """
    for item in namespace.Items():
        try:
            if name_substring.lower() in (item.Name or "").lower():
                return item
        except Exception:
            # skip objects that don't expose Name
            continue
    return None


def list_top_level_folders_and_counts(device_item) -> List[Tuple[str, int]]:
    """Given a device COM item, list its top-level folder names and counts of non-folder items inside each.

    The iPhone usually exposes: Internal Storage -> DCIM or custom folders. This function does a shallow traversal
    (device -> children -> grandchildren) to reach folders that actually contain files.
    """
    out: List[Tuple[str, int]] = []
    shell = win32com.client.Dispatch("Shell.Application")

    try:
        # Get the device folder object and its items
        dev_folder = device_item.GetFolder()
        root_items = list(dev_folder.Items())
    except Exception:
        # Some devices expose Items directly
        try:
            root_items = list(device_item.Items())
        except Exception:
            return out

    # Iterate children (e.g., "Internal Storage") and then their children (actual photo folders)
    for child in root_items:
        try:
            # many child objects are folders; get their folder and iterate
            if getattr(child, "IsFolder", False):
                try:
                    child_folder = child.GetFolder()
                    for sub in list(child_folder.Items()):
                        # We expect photo folders here (e.g., '202503__' or '100APPLE')
                        name = getattr(sub, "Name", None)
                        if not name:
                            continue
                        # count non-folder items inside this subfolder
                        try:
                            sf = sub.GetFolder()
                            items_inside = list(sf.Items())
                            count = sum(1 for x in items_inside if not getattr(x, "IsFolder", False))
                        except Exception:
                            # Could not open sub folder; mark as -1
                            count = -1
                        out.append((name, count))
                except Exception:
                    # unable to .GetFolder() on child - skip
                    continue
            else:
                # non-folder at root level - skip
                continue
        except Exception:
            continue

    return out


def main() -> int:
    shell = win32com.client.Dispatch("Shell.Application")
    mycomp = get_my_computer_namespace(shell)
    if mycomp is None:
        print("Could not access 'This PC' namespace. Are you running on Windows?")
        return 3

    device = find_device_item(mycomp, "iphone")
    if device is None:
        print("No iPhone found under 'This PC'. Make sure the phone is unlocked and 'Trust' was accepted.")
        return 4

    print("Found device:", device.Name)
    results = list_top_level_folders_and_counts(device)
    if not results:
        print("No accessible photo folders found. Try opening the device in Explorer once to initialise it.")
        return 5

    print()
    print("Folder name -> file count")
    print("---------------------------")
    for name, cnt in results:
        if cnt >= 0:
            print(f"{name} -> {cnt}")
        else:
            print(f"{name} -> (count unavailable)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
