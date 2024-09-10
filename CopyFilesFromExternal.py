import os
import csv
import hashlib
import re
import shutil
import sys
import concurrent.futures
#from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel
from tqdm import tqdm
from termcolor import colored, cprint
from datetime import datetime

def get_hash_csv(path):
    chunk_size = 134200000  # original 65535=64KB, you can adjust this value based on your needs
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
    source_csv_data = []  # List to store CSV data

    with open(os.path.join(source_path, 'hashes.csv'), 'r') as source_file:
        reader = csv.DictReader(source_file)
        source_csv_data = list(reader)  # Read the CSV data into a list
        for row in source_csv_data:
            source_hashes[row['FileName']] = row['Hash']

    destination_hashes = {}
    destination_csv_data = []  # List to store CSV data

    with open(os.path.join(destination_path, 'hashes.csv'), 'r') as destination_file:
        reader = csv.DictReader(destination_file)
        destination_csv_data = list(reader)  # Read the CSV data into a list
        for row in destination_csv_data:
            destination_hashes[row['FileName']] = row['Hash']

    missing_files = set(source_hashes.keys()) - set(destination_hashes.keys())
    if missing_files:
        print(colored("The following files are missing in the destination folder:", "light_red", attrs=["blink"]))
        for filename in missing_files:
            print(colored(filename, "light_red"))

    changed_files = [filename for filename, hash_value in source_hashes.items() if hash_value != destination_hashes.get(filename, None)]
    if changed_files:
        print(colored("The following files have been modified:", 'yellow', attrs=["blink"]))
        for filename in changed_files:
            # Search the source_csv_data list for the file path
            file_path = next((row['Path'] for row in source_csv_data if row['FileName'] == filename), None)
            print(f"{file_path} - {source_hashes[filename]}")
    else:
        print(colored("No files have been modified.", 'light_green'))
def copy_files(source_folder, destination_folder):
    # List all files to be copied
    files_to_copy = []
    for root, dirs, files in os.walk(source_folder):
        for file in files:
            source_path = os.path.join(root, file)
            relative_path = os.path.relpath(source_path, source_folder)
            destination_path = os.path.join(destination_folder, relative_path)
            files_to_copy.append((source_path, destination_path))
    total_size_mb = sum(os.path.getsize(src) / (1024 * 1024) for src, _ in files_to_copy)

# Create the destination directories if they don't exist
    for _, destination_path in files_to_copy:
        destination_dir = os.path.dirname(destination_path)
        os.makedirs(destination_dir, exist_ok=True)
   
    # Define the format for total and current values
    fmt = "{total:.0f}MB [{percentage:.0f}%] | {n:.0f}/{total:.0f}MB | ETA: {remaining}s"

    # Copy files with a progress bar
    with tqdm(total=total_size_mb, unit="MB", desc="Copying", bar_format=fmt) as pbar:
        for source_path, destination_path in files_to_copy:
            shutil.copy2(source_path, destination_path)  # Use shutil.copy2 to preserve metadata
            pbar.update(os.path.getsize(source_path) / (1024 * 1024))  # Update progress based on MB copied

def check_storage(source_folder, destination_drive):
    # Calculate total size of the source folder
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(source_folder):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    
    total_size_gb = total_size / (1024 * 1024 * 1024)
    print(colored(f"Total size of the source folder: {total_size_gb:.2f} GB", "light_blue"))

    # Get free space in the destination drive
    statvfs = os.statvfs(destination_drive)
    free_space = statvfs.f_frsize * statvfs.f_bavail
    free_space_gb = free_space / (1024 * 1024 * 1024)
    print(colored(f"Free space in the destination drive: {free_space_gb:.2f} GB", "light_blue"))

    if total_size_gb > free_space_gb:
        print(colored("Not enough free space in the destination drive.", "light_red", attrs=["blink"]))
        return False
    return True

def delete_oldest_folder(destination_path):
    date_pattern = r'^\d{4}-\d{2}-\d{2}\s.*$'
    
    # List all directories in the destination path
    folders = [folder for folder in os.listdir(destination_path) if os.path.isdir(os.path.join(destination_path, folder)) and re.match(date_pattern, folder)]
    
    # Check if there are no matching folders
    if not folders:
        print(colored("No folders with the specified date pattern found.", "light_red"))
        return

    # Sort folders by the date in their name
    oldest_folder = sorted(folders, key=lambda folder: datetime.strptime(folder.split()[0], '%Y-%m-%d'))[0]

    prompt = input(colored(f"The oldest folder is '{oldest_folder}'. Do you want to delete it to free up space? (y/n): ", "yellow"))
    if prompt.lower() == 'y':
        try:
            shutil.rmtree(os.path.join(destination_path, oldest_folder))
            print(colored(f"Deleted folder '{oldest_folder}'.", "light_green"))
        except FileNotFoundError:
            print(colored(f"Folder '{oldest_folder}' not found, possibly already deleted.", "light_red"))
    else:
        print(colored("Oldest folder not deleted.", "light_red"))

# Define the source and destination paths
source_path = "/media/andorus/Audio_Projects/"
destination_path = "/media/andorus/AudioProjects/Audio Projects/"

# Get the most recent folder based on the date in the folder name
date_pattern = r'^\d{4}-\d{2}-\d{2}\s.*$'
most_recent_folder = sorted(
    [folder for folder in os.listdir(source_path) if os.path.isdir(os.path.join(source_path, folder)) and re.match(date_pattern, folder)],
    key=lambda folder: datetime.strptime(folder.split()[0], '%Y-%m-%d'),
    reverse=True
)[0]
source_folder = os.path.join(source_path, most_recent_folder)
destination_folder = os.path.join(destination_path, most_recent_folder)

# Check if there is enough space in the destination folder
if not check_storage(source_folder, destination_path):
    delete_oldest_folder(destination_path)
    if not check_storage(source_folder, destination_path):
        print(colored("Still not enough free space after deletion. Aborting operation.", "light_red", attrs=["blink"]))
        sys.exit(1)

copy_or_compare = input("Would you like to copy the files (y) or only attempt to compare existing hashes (n)? ")

if copy_or_compare == "y":
    print(colored(f"Copying folder {os.path.join(source_path, most_recent_folder)} to internal storage","light_green"))
    # Copy the most recent folder to the destination path
    #shutil.copytree(os.path.join(source_path, most_recent_folder), os.path.join(destination_path, most_recent_folder), dirs_exist_ok=True)
    copy_files(source_folder, destination_folder)



source_hashes_exist = os.path.exists(os.path.join(source_folder, 'hashes.csv'))
destination_hashes_exist = os.path.exists(os.path.join(destination_folder, 'hashes.csv'))
if source_hashes_exist and destination_hashes_exist:
        regenerate_or_compare = input("Hashes.csv files already exist in both locations. Do you want to re-generate hashes (r) or compare existing hashes (c)? ")
        if regenerate_or_compare == 'r':
            print(colored("RE-GENERATING FILE HASHES. PLEASE WAIT AS THIS WILL TAKE A MINUTE.", "yellow"))
            get_hash_csv(source_folder)
            get_hash_csv(destination_folder)
            print(colored("Comparing existing file hashes.", "light_yellow"))
            compare_hashes_csv(source_folder, destination_folder)
        elif regenerate_or_compare == 'c':
            print(colored("Comparing existing file hashes.", "light_yellow"))
            compare_hashes_csv(source_folder, destination_folder)
        else:
            print(colored("Invalid input. Please enter 'r' to re-generate hashes or 'c' to compare existing hashes.", "red"))

elif source_hashes_exist:
        print(colored("Copying folder to internal storage.", "light_green"))
        #shutil.copytree(os.path.join(source_path, most_recent_folder), os.path.join(destination_path, most_recent_folder), dirs_exist_ok=True)
        copy_files(source_folder, destination_folder)

        print(colored("Generating file hashes for source folder.", "yellow"))
        get_hash_csv(source_folder)
        get_hash_csv(destination_folder)

        print(colored("Comparing file hashes.", "light_yellow"))
        compare_hashes_csv(source_folder, destination_folder)

else:
    print(colored("GENERATING FILE HASHES, PLEASE WAIT AS THIS WILL TAKE A MINUTE.", "yellow"))
    # Create a ThreadPoolExecutor
    with concurrent.futures.ThreadPoolExecutor() as executor:
    # Submit the tasks to the executor
        futures = [executor.submit(get_hash_csv, path) for path in [source_folder, destination_folder]]

        # Wait for all tasks to complete
        concurrent.futures.wait(futures)
    
    #commented for reversion
    #get_hash_csv(source_folder)
    #get_hash_csv(destination_folder)

    print(colored("COMPARING FILE HASHES TO ENSURE INTEGRITY OF COPIED FILES.", "light_yellow"))
    compare_hashes_csv(source_folder, destination_folder) 
