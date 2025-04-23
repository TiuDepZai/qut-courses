import fitz  # PyMuPDF
import json
import re
import sys


def fix_split_codes(text):
    """
    Fixes unit codes split across lines (e.g., 'ABB\\n101' becomes 'ABB101').
    """
    return re.sub(r'([A-Z]{3})\s*\n\s*(\d{3})', r'\1\2', text)


def extract_course_info_from_dict(pdf_path, course_code):
    """
    Extracts semester and unit code information from a PDF using PyMuPDF's 'dict' layout.
    """
    doc = fitz.open(pdf_path)
    full_text = ""

    # Combine all pages into a single text blob
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        full_text += page.get_text("text") + "\n\n"
    doc.close()

    # Fix broken unit codes (e.g., ABB\n105)
    full_text = fix_split_codes(full_text)

    # Extract all semester sections
    semester_matches = list(re.finditer(
        r"(Year\s+\d,?\s+Semester\s+\d(?:\s+\(July\))?)", full_text, re.IGNORECASE))

    course_data = {
        "course_code": course_code,
        "structures": [
            {
                "name": f"{course_code} - default structure",
                "semesters": {}
            }
        ]
    }

    semesters = course_data["structures"][0]["semesters"]

    for i, match in enumerate(semester_matches):
        semester_title = match.group(1)
        start_idx = match.end()
        end_idx = semester_matches[i + 1].start() if i + 1 < len(semester_matches) else len(full_text)

        semester_block = full_text[start_idx:end_idx]
        semester_key = semester_title.lower().replace(" ", "").replace(",", "")

        unit_codes = re.findall(r'ABB\d{3}', semester_block)
        qut_you_units = re.findall(r'Select one QUT You unit', semester_block)
        complementary_unit = "Complementary Studies unit" if "Complementary Studies unit" in semester_block else None

        if unit_codes or qut_you_units or complementary_unit:
            semesters[semester_key] = unit_codes
            semesters[semester_key].extend(["Select one QUT You unit"] * len(qut_you_units))
            if complementary_unit:
                semesters[semester_key].append(complementary_unit)

    return course_data


def save_course_info_to_json(course_data, output_json):
    """
    Saves the extracted course data to a JSON file.
    """
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(course_data, f, indent=4)
    print(f" Data extracted and saved to {output_json}")


course_code = sys.argv[1].upper()
pdf_path = f"./pdf/{course_code}.pdf"
output_json = f"{course_code}_course_data.json"

course_info = extract_course_info_from_dict(pdf_path, course_code)
save_course_info_to_json(course_info, output_json)
