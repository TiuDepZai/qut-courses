import fitz  # PyMuPDF
import re
import json
import os
import sys
import traceback

def fix_split_codes(text):
    """
    Fixes unit codes that might be split across lines.
    For example, 'ABB\n101' becomes 'ABB101'.
    """
    return re.sub(r'([A-Z]{3})\s*\n\s*(\d{3})', r'\1\2', text)


def extract_course_guide_info_from_text(text):
    """
    Extracts Accurate Date, Structures, and Year/Semester course data.
    """
    structures = []

    # Find all structure blocks (e.g., "AB05 - February entry - Full Time")
    structure_matches = re.findall(r'(AB05 - .*?entry - .*?)\s*\n\s*Semesters', text)

    for structure_name in structure_matches:
        # Extract the content for the current structure
        structure_content = re.search(
            rf'{re.escape(structure_name)}\s*\n\s*Semesters(.*?)(?=AB05 - |$)',
            text,
            re.DOTALL
        )
        if not structure_content:
            continue

        structure_text = structure_content.group(1)

        # Extract semesters and their units
        semesters = {}
        semester_blocks = re.split(r'Year\s+\d,?\s+Semester\s+\d(?:\s+\(July\))?', structure_text)
        semester_titles = re.findall(r'Year\s+\d,?\s+Semester\s+\d(?:\s+\(July\))?', structure_text)

        for title, block in zip(semester_titles, semester_blocks[1:]):
            semester_key = title.lower().replace(" ", "").replace(",", "")
            unit_codes = re.findall(r'(ABB\d{3})', block)
            semesters[semester_key] = unit_codes

        # Add the structure to the list
        structures.append({
            "name": structure_name,
            "semesters": semesters
        })

    return {
        "course_code": "AB05",  # Hardcoded for now; replace with dynamic extraction if needed
        "structures": structures
    }


def extract_and_save_course_info(pdf_path, output_json):
    try:
        doc = fitz.open(pdf_path)
        full_text = ""
        for page_num in range(len(doc)):
            page = doc[page_num]
            full_text += page.get_text("text") + "\n\n"
        doc.close()

        full_text = fix_split_codes(full_text)

        course_info = extract_course_guide_info_from_text(full_text)

        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(course_info, f, indent=4)

        print(f"Extraction complete. Saved to {output_json}")
    except Exception as e:
        print(f"Error extracting course info: {e}")
        traceback.print_exc()



# Entry point
pdf_courseCode = sys.argv[1]
pdf_path = "./pdf/temp.pdf"
output_file = f"./pdf/{os.path.splitext(pdf_courseCode)[0]}_course_data.json"
extract_and_save_course_info(pdf_path, output_file)
