import fitz
import re
import json
import sys
import os

def normalize_semester(sem):
    """Remove anything in parentheses and extra spaces, then lowercase."""
    return re.sub(r'\s*\(.*?\)', '', sem).strip().lower()

def dedup_preserve_order(seq):
    seen = set()
    result = []
    for x in seq:
        x_lower = x.lower()
        if x_lower not in seen:
            seen.add(x_lower)
            result.append(x_lower)
    return result

def extract_units_by_semester(pdf_path, semester_blocks):
    doc = fitz.open(pdf_path)
    semester_header_pattern = re.compile(r'Year\s*\d+,\s*Semester\s*\d+', re.IGNORECASE)
    unit_code_pattern = re.compile(r'^[A-Z]{3}\d{3}$')
    special_unit_pattern = re.compile(r'(QUT You unit|Complementary Studies unit)', re.IGNORECASE)


    all_semesters = set()
    for block in semester_blocks:
        all_semesters.update([normalize_semester(s) for s in block["semesters"]])

    semester_units = {sem: [] for sem in all_semesters}
    current_semester = None
    pre_semester_units = []

    for page in doc:
        tables = page.find_tables()
        if not tables:
            continue
        for table in tables:
            table_data = table.extract()
            for row in table_data:
                cleaned_row = [str(cell).strip() if cell else "" for cell in row]
                if cleaned_row[0] and semester_header_pattern.match(cleaned_row[0]):
                    normalized_sem = normalize_semester(cleaned_row[0])
                    if normalized_sem in semester_units:
                        current_semester = normalized_sem
                    else:
                        current_semester = None
                    continue
                if current_semester and cleaned_row[0] and unit_code_pattern.match(cleaned_row[0]):
                    title = next((cell for cell in cleaned_row[1:] if cell), "")
                    semester_units[current_semester].append({
                        "code": cleaned_row[0],
                        "title": title
                    })
                elif not current_semester and cleaned_row[0] and unit_code_pattern.match(cleaned_row[0]):
                    title = next((cell for cell in cleaned_row[1:] if cell), "")
                    pre_semester_units.append({
                        "code": cleaned_row[0],
                        "title": title
                    })
                elif not current_semester and cleaned_row[0] and special_unit_pattern.search(cleaned_row[0]):
                    pre_semester_units.append({
                        "code": cleaned_row[0],
                        "title": ""
                    })


    y1s1_norm = normalize_semester("year 1, semester 1")
    if y1s1_norm in semester_units and not semester_units[y1s1_norm]:
        semester_units[y1s1_norm] = pre_semester_units

    doc.close()


    # Build the output structure for the unit guide
    unit_guide = []
    for block in semester_blocks:
        sem_units = {}
        for sem in block["semesters"]:
            sem_norm = normalize_semester(sem)
            if sem_norm in semester_units:
                sem_units[sem] = semester_units[sem_norm]
        unit_guide.append({
            "mode_entry": block["mode_entry"],
            "units": sem_units
        })

    return unit_guide

if __name__ == "__main__":
    course_code = sys.argv[1].upper()
    pdf_path = f"./pdf/{course_code}.pdf"
    json_path = f"./courses/{course_code}.json"
    output_json = f"./course_to_unit/{course_code}_unitGuide.json"

    # Load semester_blocks from the course JSON
    with open(json_path, "r", encoding="utf-8") as f:
        course_data = json.load(f)
    semester_blocks = course_data.get("semester_blocks", [])

    # Extract the unit guide
    unit_guide = extract_units_by_semester(pdf_path, semester_blocks)

    # Output as {AB05_unitGuide: [...]}
    # result = {f"{course_code}_unitGuide": unit_guide}
    # os.makedirs(os.path.dirname(output_json), exist_ok=True)
    # with open(output_json, "w", encoding="utf-8") as f:
    #     json.dump(result, f, indent=2)

    print(f"Wrote {output_json}")