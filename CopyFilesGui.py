import os
import csv
import hashlib
import re
import shutil
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel

from termcolor import colored, cprint
from datetime import datetime

def get_hash_csv(path):
    chunk_size = 33560000  # original 65535=64KB, you can adjust this value based on your needs
    files = []

    for root, _, filenames in os.walk(path):
        for filename in filenames:
            file_path = os.path.join(root, filename)
            if os.path.isfile(file_path) and filename != 'hashes.csv':
                files.append(file_path)

    try:
        with open(os.path.join(path, 'hashes.csv'), 'w', newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(['Path', 'FileName', 'Hash'])
            for file_path in files:
                file_hash = hashlib.sha256()
                with open(file_path, 'rb') as file:
                    while chunk := file.read(chunk_size):
                        file_hash.update(chunk)

                writer.writerow([file_path, os.path.basename(file_path), file_hash.hexdigest()])
    except OSError:
        print(colored(f"Could not write to {os.path.join(path, 'hashes.csv')}, aborting","light_red", attrs=["blink"]))
        return

    print(colored(f"File hashes for {path} generated and stored in hashes.csv", "light_yellow"))

def compare_hashes_csv(source_path, destination_path):
    source_hashes = {}
    with open(os.path.join(source_path, 'hashes.csv'), 'r') as source_file:
        reader = csv.DictReader(source_file)
        for row in reader:
            source_hashes[row['FileName']] = row['Hash']

    destination_hashes = {}
    with open(os.path.join(destination_path, 'hashes.csv'), 'r') as destination_file:
        reader = csv.DictReader(destination_file)
        for row in reader:
            destination_hashes[row['FileName']] = row['Hash']

    missing_files = set(source_hashes.keys()) - set(destination_hashes.keys())
    if missing_files:
        print(colored("The following files are missing in the destination folder:","light_red", attrs=["blink"]))
        for filename in missing_files:
            print(colored(filename,"light_red"))

    changed_files = [filename for filename, hash_value in source_hashes.items() if hash_value != destination_hashes.get(filename, None)]
    if changed_files:
        print(colored("The following files have been modified:", 'yellow', attrs=["blink"]))
        for filename in changed_files:
            file_path = next((row['Path'] for row in reader if row['FileName'] == filename), None)
            print(f"{file_path} - {source_hashes[filename]}")
    else:
        print(colored("No files have been modified.",'light_green'))

# Define the source and destination paths
source_path = "/media/andorus/Audio_Projects"
destination_path = "/media/andorus/More Games2/Audio Projects/"

# Get the most recent folder based on the date in the folder name
date_pattern = r'^\d{4}-\d{2}-\d{2}\s.*$'
most_recent_folder = sorted(
    [folder for folder in os.listdir(source_path) if os.path.isdir(os.path.join(source_path, folder)) and re.match(date_pattern, folder)],
    key=lambda folder: datetime.strptime(folder.split()[0], '%Y-%m-%d'),
    reverse=True
)[0]

#copy_or_compare = input("Would you like to copy the files (y) or only attempt to compare existing hashes (n)? ")

class UserPrompt(QWidget):
    def __init__(self):
        super().__init__()

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        label = QLabel("Would you like to copy the files or compare hashes?")
        layout.addWidget(label)

        copy_button = QPushButton("Copy Files")
        copy_button.clicked.connect(self.copy_files)
        layout.addWidget(copy_button)

        compare_button = QPushButton("Compare Hashes")
        compare_button.clicked.connect(self.compare_hashes)
        layout.addWidget(compare_button)

        self.setLayout(layout)
        self.setWindowTitle("File Operations Prompt")

    def copy_files(self):
        # Perform copy operation or call the relevant function
        print("User selected to copy files")
        self.close()

    def compare_hashes(self):
        # Perform compare operation or call the relevant function
        print("User selected to compare hashes")
        self.close()

def main():
    app = QApplication(sys.argv)
    window = UserPrompt()
    window.show()

    # Wait until external storage is connected
    while True:
        app.processEvents()
        time.sleep(2)  # Adjust the time interval as needed

        external_storage_path = "/media/andorus/Audio_Projects/"  # Replace with your external storage path
        if os.path.exists(external_storage_path):
            window.close()
            break

    # Once the external storage is connected, proceed to the main script
    # Your main script logic can be placed here

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()


if copy_or_compare == "y":
    print(colored(f"Copying folder {os.path.join(source_path, most_recent_folder)} to internal storage","light_green"))
    # Copy the most recent folder to the destination path
    shutil.copytree(os.path.join(source_path, most_recent_folder), os.path.join(destination_path, most_recent_folder), dirs_exist_ok=True)

source_folder = os.path.join(source_path, most_recent_folder)
destination_folder = os.path.join(destination_path, most_recent_folder)

print(colored("GENERATING FILE HASHES, PLEASE WAIT AS THIS WILL TAKE A MINUTE.", "yellow"))
get_hash_csv(source_folder)
get_hash_csv(destination_folder)

print(colored("COMPARING FILE HASHES TO ENSURE INTEGRITY OF COPIED FILES.", "light_yellow"))
compare_hashes_csv(source_folder, destination_folder) 
 
