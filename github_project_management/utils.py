import csv

from github_project_management.constants import HEADER


def save_as_csv(rows, filename):
    with open(filename, 'w') as f:
        writer = csv.writer(f)
        writer.writerow(HEADER)
        for row in rows:
            writer.writerow([row[col] for col in HEADER])
