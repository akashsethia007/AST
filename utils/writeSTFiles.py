import csv
import os


def writeSTFiles(path, st_list):
    """Write a list of dicts to a CSV file, creating parent directories as needed."""
    if not st_list:
        return

    os.makedirs(os.path.dirname(path), exist_ok=True)
    fieldnames = list(st_list[0].keys())

    with open(path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(st_list)
