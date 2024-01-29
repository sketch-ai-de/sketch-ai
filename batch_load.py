import os
import subprocess

TARGET_DIRECTORY = "docs"
FILE_PATH = "already_loaded_data.txt"

try:
    with open(FILE_PATH, "r") as file_to_read:
        already_loaded_data_list = [line.strip() for line in file_to_read]
except FileNotFoundError:
    print(f"File '{FILE_PATH}' not found.")
except IOError:
    print(f"Error reading file '{FILE_PATH}'.")


def path_generator(target_directory):
    url_list = []
    for root, _, files in os.walk(target_directory):
        for file in files:
            if any(ext in file for ext in ["hw.json", "sw.json"]):
                url_list.append(os.path.join(root, file))
    return url_list


file_url_list = path_generator(TARGET_DIRECTORY)

for file_url in file_url_list:
    if file_url in already_loaded_data_list:
        print(f"File {file_url} already loaded.")
        continue
    try:
        print(f"Loading file_url: {file_url}")
        command = [
            "python3",
            "load_data.py",
            "-l",
            "openai",
            "-j",
            file_url,
        ]
        subprocess.check_output(command)
        with open(FILE_PATH, "a") as file_to_write:
            file_to_write.write(file_url + "\n")
    except subprocess.CalledProcessError:
        print(f"Error in loading file_url: {file_url}")
