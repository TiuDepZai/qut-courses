import os
import json

# Load the JSON file
with open("courses.json", "r", encoding="utf-8") as file:
    data = json.load(file)

# Count the number of entries in the "list_of_courses"
number_of_courses = len(data["list_of_courses"])

print(f"Number of courses in courses: {number_of_courses}")

with open("not_courses.json", "r", encoding="utf-8") as file:
    Notdata = json.load(file)

number_of_not_courses = len(Notdata)

print(f"Number of not courses in courses: {number_of_not_courses}")

# Specify the folder path
folder_path = "./courses"  # Replace with your folder path

# Count the number of files in the folder
number_of_files = len([file for file in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, file))])

print(f"Number of files in '{folder_path}': {number_of_files}")

