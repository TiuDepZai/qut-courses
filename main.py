import subprocess
import os
import asyncio
import json
import sys


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

    
    first = data['list_of_courses'][0]

    # await run_script_with_args("scripts/extract_course_information.py", first['courseCode'], first['course_title'])
    i = 0
    for course in data['list_of_courses']:
        course_code = course['courseCode']
        course_title = course['course_title']

        # Pass course information as arguments to the script
        await run_script_with_args("scripts/ECI.py", course_code, course_title)
        await asyncio.sleep(2)
        i += 1
        if i > 50:
            break

async def pull_unit_information():
    # Open and load the JSON file
    with open("units.json", "r", encoding="utf-8") as file:
        data = json.load(file)  # Load JSON data into a Python object (list or dict)
    
    for unitCode in data['unitCodes']:
        unitCode = unitCode['unitCode']

        # Pass course information as arguments to the script
        await run_script_with_args("scripts/EUI.py", unitCode)
        await asyncio.sleep(2)
        


# Main script
async def main():
    
    # Check if there is a course json file with all the course information.
    # await check_and_run()

    # Run the script to pull course information
    # await pull_course_information()

    await pull_unit_information()

# Run the main function
asyncio.run(main())