import fitz  # PyMuPDF
import pymupdf
import json
import re
import sys

def dedup_preserve_order(seq):
    seen = set()
    result = []
    for x in seq:
        x_lower = x.lower()
        if x_lower not in seen:
            seen.add(x_lower)
            result.append(x_lower)
    return result

def extract_mode_entry_and_semesters(pdf_path):
    doc = fitz.open(pdf_path)
    mode_entry_pattern = re.compile(
        r'(February|July) entry\s*-\s*(Full Time|Part Time)', re.IGNORECASE
    )
    semester_pattern = re.compile(
        r'Year\s*\d+,\s*Semester\s*\d+', re.IGNORECASE
    )

    results = []
    for page in doc:
        text = page.get_text("text")
        # Find all mode/entry headers and their positions
        mode_entries = [(m.start(), m.group(1).capitalize(), m.group(2).title()) for m in mode_entry_pattern.finditer(text)]
        # Add an artificial end marker for the last block
        mode_entries.append((len(text), None, None))

        for i in range(len(mode_entries) - 1):
            start, entry_time, mode = mode_entries[i]
            end, _, _ = mode_entries[i + 1]
            block = text[start:end]

            # Only process if this is a real mode/entry header
            if entry_time and mode:
                semesters = semester_pattern.findall(block)
                semesters = dedup_preserve_order(semesters)
                # Only keep blocks that actually have semesters listed
                if semesters:
                    results.append({
                        "mode_entry": {
                            "entry_time": entry_time,
                            "mode": mode
                        },
                        "semesters": semesters
                    })

    doc.close()
    return results


def save_course_info_to_json(course_data, output_json):
    """
    Saves the extracted course data to a JSON file.
    """
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(course_data, f, indent=4)
    print(f" Data extracted and saved to {output_json}")


def add_semester_blocks_to_course(course_json_path, semester_blocks, output_path=None):
    # Load the course JSON
    with open(course_json_path, "r", encoding="utf-8") as f:
        course_data = json.load(f)

    # Add the semester blocks under durations
    course_data["semester_blocks"] = semester_blocks

    # Save to a new file or overwrite
    if output_path is None:
        output_path = course_json_path
        
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(course_data, f, indent=2)

    print(f"Semester blocks added to {output_path}")


course_code = sys.argv[1].upper()
pdf_path = f"./pdf/{course_code}.pdf"
json_path = f"./courses/{course_code}.json"
output_json = f"./course_to_unit/{course_code}_course_data.json"

course_info = extract_mode_entry_and_semesters(pdf_path)
add_semester_blocks_to_course(json_path, course_info)
