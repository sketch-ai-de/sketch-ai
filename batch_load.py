import os
import subprocess

target_directory = "docs"
file_path = "already_loaded_data.txt"

try:
    with open(file_path, "r") as file_to_read:
        already_loaded_data_list = [line.strip() for line in file_to_read]
except FileNotFoundError:
    print(f"File '{file_path}' not found.")
except IOError:
    print(f"Error reading file '{file_path}'.")


def path_generator(target_directory):
    url_list = []
    for root, dirs, files in os.walk(target_directory):
        for file in files:
            if any(ext in file for ext in ["hw.json", "sw.json"]):
                url_list.append(os.path.join(root, file))
    return url_list


files = path_generator(target_directory)

for file in files:
    if file in already_loaded_data_list:
        print(f"File {file} already loaded.")
        continue
    try:
        print(f"Loading file: {file}")
        command = [
            "python3",
            "load_data.py",
            "-l",
            "openai",
            "-j",
            file,
        ]
        subprocess.check_output(command)
        with open(file_path, "a") as file_to_write:
            file_to_write.write(file + "\n")
    except subprocess.CalledProcessError:
        print(f"Error in loading file: {file}")
