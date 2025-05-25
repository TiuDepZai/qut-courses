import fitz  # PyMuPDF
import re
import json
import os
import sys
import traceback

# Hard cut: always stop here
HARD_CUTOFFS = [
    "Unit Synopses",
    "Unit Lists"
]

# Soft cut: only stop if not likely part of a wrapped title
SOFT_CUTOFFS = [
    "Interior",
    "Landscape",
    "Construction",
    "Planning"
]


def fix_split_codes(text):
    """
    Fixes unit codes that might be split across lines.
    Example: 'ABB\\n101' becomes 'ABB101'.
    """
    return re.sub(r'([A-Z]{3})\s*\n\s*(\d{3})', r'\1\2', text)


def find_cutoff_index_by_line(text, soft_keywords, hard_keywords):
    """
    Finds the first index in `text` where a keyword appears as its own line.
    - HARD keywords always trigger a cut.
    - SOFT keywords are ignored if a unit code appears in nearby lines.
    """
    lines = text.splitlines()
    for i, line in enumerate(lines):
        stripped = line.strip()

        # HARD cutoff — always stop
        if stripped in hard_keywords:
            return sum(len(lines[j]) + 1 for j in range(i))

        # SOFT cutoff — check previous few lines for ABB code
        if stripped in soft_keywords:
            context = "\n".join(lines[max(0, i-2):i])
            if not re.search(r'ABB\d{3}', context):
                return sum(len(lines[j]) + 1 for j in range(i))

    return -1


def extract_course_guide_info_from_text(text, course_code):
    """
    Extracts structure blocks for a given course code (e.g., AB05),
    and collects semesters and unit codes within each structure.
    """
    structures = []
    pattern = rf'({course_code} - .*?entry - .*?)\s*\n\s*Semesters'
    structure_matches = list(re.finditer(pattern, text))

    for idx, match in enumerate(structure_matches):
        structure_name = match.group(1)
        start = match.end()

        end = structure_matches[idx + 1].start() if idx + 1 < len(structure_matches) else len(text)
        structure_text = text[start:end]

        # Apply smart cutoff
        cutoff_index = find_cutoff_index_by_line(structure_text, SOFT_CUTOFFS, HARD_CUTOFFS)
        if cutoff_index != -1:
            structure_text = structure_text[:cutoff_index]

        # Extract semesters
        semesters = {}
        semester_blocks = re.split(r'Year\s+\d,?\s+Semester\s+\d(?:\s+\(July\))?', structure_text)
        semester_titles = re.findall(r'Year\s+\d,?\s+Semester\s+\d(?:\s+\(July\))?', structure_text)

        for title, block in zip(semester_titles, semester_blocks[1:]):
            semester_key = title.lower().replace(" ", "").replace(",", "")
            unit_codes = re.findall(r'(ABB\d{3})', block)

            unit_codes.extend(["Select one QUT You unit"] * len(re.findall(r'Select one QUT You unit', block)))
            if re.search(r'Complementary Studies unit', block, re.IGNORECASE):
                unit_codes.append("Complementary Studies unit")

            if unit_codes:
                semesters[semester_key] = unit_codes

        if semesters:
            structures.append({
                "name": structure_name,
                "semesters": semesters
            })

    return {
        "course_code": course_code,
        "structures": structures
    }


def extract_and_save_course_info(pdf_path, output_json, course_code):
    try:
        doc = fitz.open(pdf_path)
        full_text = ""
        for page_num in range(len(doc)):
            page = doc[page_num]
            full_text += page.get_text("text") + "\n\n"
        doc.close()

        full_text = fix_split_codes(full_text)
        course_info = extract_course_guide_info_from_text(full_text, course_code)

        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(course_info, f, indent=4)

        print(f" Extraction complete. Saved to {output_json}")
    except Exception as e:
        print(f" Error extracting course info: {e}")
        traceback.print_exc()


# Entry point
# Usage: python extract.py AB05


course_code = sys.argv[1].upper()
pdf_path = "./pdf/temp.pdf"
output_file = f"./pdf/{course_code}_course_data.json"

extract_and_save_course_info(pdf_path, output_file, course_code)
