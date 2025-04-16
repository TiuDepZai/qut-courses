import json

# Load the JSON file
with open("courses.json", "r", encoding="utf-8") as file:
    data = json.load(file)

# Count the number of entries in the "list_of_courses"
number_of_courses = len(data["list_of_courses"])

print(f"Number of courses: {number_of_courses}")