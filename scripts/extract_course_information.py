# The purpose of this script is to pull information from the each course information.import sys
import sys



if __name__ == "__main__":
    # Access arguments passed to the script
    course_code = sys.argv[1]  # First argument
    course_title = sys.argv[2]  # Second argument

    formatted_course_title = course_title.lower().replace(" ", "-")

    courseLink = f"https://www.qut.edu.au/courses/{formatted_course_title}"

    print(f"Processing course: {course_code} - {courseLink}")
    # Add your processing logic here