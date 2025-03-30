import subprocess
import os
import asyncio

# Async function for running scripts
async def run_script(script_name): 
    # Run subprocess that won't block event loop
    process = await asyncio.create_subprocess_exec(
        "python3", script_name, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
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

# Check if active_courses_list.txt exists. If it doesn't then get it
async def check_and_run():
    if os.path.exists("active_courses_list.txt"):
        print("active_courses_list.txt already exists")
    else:
        print("active_courses_list.txt does not exist. Fetching the list...")
        await run_script("scripts/PCI.py")

# Main script
async def main():
    await check_and_run()

# Run the main function
asyncio.run(main())