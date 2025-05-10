import subprocess
import os
import asyncio
import json
import sys
import math


# Async function for running scripts
async def run_script(script_name): 
    # Run subprocess that won't block event loop
    process = await asyncio.create_subprocess_exec(

        # For Linux
        # "python3", script_name, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE

        # For Windows
        sys.executable, script_name, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE

    )

    # Wait for process to finish and capture output
    stdout, stderr = await process.communicate()

    # Check the return code to determine if the script ran successfully
    if process.returncode == 0:
        print(f"Script {script_name} completed successfully.")
        print(stdout.decode())
    else:
        print(f"Script {script_name} failed with error code {process.returncode}.")
        print(stderr.decode())

# Function to run a script with arguments
async def run_script_with_args(script_name, *args):
    # Run subprocess with arguments
    process = await asyncio.create_subprocess_exec(
        # For Linux
        # "python3", script_name, *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE

        # For Windows
        sys.executable, script_name, *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE

    )

    # Wait for process to finish and capture output
    stdout, stderr = await process.communicate()

    # Check the return code to determine if the script ran successfully
    if process.returncode == 0:
        print(f"Script {script_name} completed successfully with args: {args}")
        print(stdout.decode(errors='replace'))
    else:
        print(f"Script {script_name} failed with error code {process.returncode} and args: {args}")
        print(stderr.decode(errors='replace'))

# Check if courses.json exists. If it doesn't then get it
async def check_and_run():
    if os.path.exists("courses.json"):
        print("active_courses_list.txt already exists")
    else:
        print("active_courses_list.txt does not exist. Fetching the list...")
        await run_script("scripts/PCI.py")

# Function to pull course information from the JSON file and plug into extract course information script
async def pull_course_information():

    # Open and load the JSON file
    with open("courses.json", "r", encoding="utf-8") as file:
        data = json.load(file)  # Load JSON data into a Python object (list or dict)


    # await run_script_with_args("scripts/extract_course_information.py", first['courseCode'], first['course_title'])
    for course in data['list_of_courses']:
        course_code = course['courseCode']
        course_title = course['course_title']

        # Pass course information as arguments to the script
        await run_script_with_args("scripts/ECI.py", course_code, course_title)
        await asyncio.sleep(math.random.randint(1, 5))  # Random sleep between 1 and 5 seconds

# Function to pull unitCode from course
async def pull_unitCode_from_course():
    course_folder = "./courses"

    # Check if the course folder exists
    if os.path.exists(course_folder):
        # Process each file in folder
        for filename in os.listdir(course_folder):
            # Construct the full file path
            file_path = os.path.join(course_folder, filename)
            # Check if the file is a JSON file
            if filename.endswith(".json") and os.path.isfile(file_path):
                print(f"Processing file: {file_path}")
                # Open and load the JSON file
                with open(file_path, "r", encoding="utf-8") as file:
                    try:
                        
                        course = json.load(file)
                        course_code = course['course_code']
                        course_id = course['identifier']

                        # Download course pdf to extract unitCode
                        await run_script_with_args("scripts/download_pdf.py", course_code, course_id)
                        await asyncio.sleep(2)
                        
                        # Extract information about course semesters
                        await run_script_with_args("scripts/analyze_pdf.py", course_code)
                        
                        # Extract Unit Code
                        await run_script_with_args("scripts/EUFC.py", course_code)

                        # await asyncio.sleep(2)
                        await run_script_with_args("scripts/extract_unitCodes.py", course_code)


                    except json.JSONDecodeError as e:
                        print(f"Error reading JSON file {file_path}: {e}")
                        continue


# Function to pull unit information from unit code website
async def pull_unit_information():
    # Open and load the JSON file
    with open("units.json", "r", encoding="utf-8") as file:
        data = json.load(file)  # Load JSON data into a Python object (list or dict)
    
    for unitCode in data['unitCodes']:

        # Pass course information as arguments to the script
        await run_script_with_args("scripts/EUI.py", unitCode)
        await asyncio.sleep(2)

# Main script
async def main():
    
    # # # Check if there is a course json file with all the course information.
    # await check_and_run()

    # # # Run the script to pull course information
    await pull_course_information()

    # # # Run the script to pull unit information from the PDF
    # await pull_unitCode_from_course()

    # Run script to pull unit information from unit code website
    # await pull_unit_information()

# Run the main function
asyncio.run(main())