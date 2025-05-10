import fitz  # PyMuPDF
import json
import re
import sys
import os


def extract_unit_code(pdf_path):
    """
    Extracts unique unit codes from tables in the PDF.
    """
    doc = fitz.open(pdf_path)
    unit_code_pattern = re.compile(r'^[A-Z]{3}\d{3}$')

    unique_unit_codes = set()  # To track unique unit codes globally

    for page in doc:
        tables = page.find_tables()
        if not tables:
            continue
        for table in tables:
            table_data = table.extract()
            for row in table_data:
                cleaned_row = [str(cell).strip() if cell else "" for cell in row]
                if cleaned_row[0] and unit_code_pattern.match(cleaned_row[0]):
                    unit_code = cleaned_row[0]
                    unique_unit_codes.add(unit_code)  # Add only the unit code

    doc.close()
    return list(unique_unit_codes)  # Convert the set to a list

def save_units_to_json(new_unit_codes, output_json):
    """
    Appends new unit codes to an existing JSON file or creates a new one if it doesn't exist.
    Stores the unit codes as a simple list of strings.
    """
    # Load existing data if the file exists
    if os.path.exists(output_json):
        with open(output_json, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
            existing_unit_codes = set(
                entry["unitCode"] if isinstance(entry, dict) else entry
                for entry in existing_data.get("unitCodes", []))
    else:
        existing_unit_codes = set()

    # Add new unit codes to the existing set
    updated_unit_codes = existing_unit_codes.union(new_unit_codes)

    # Save as list of strings (no dictionaries)
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump({"unitCodes": sorted(updated_unit_codes)}, f, indent=4)

    print(f"Data extracted and saved to {output_json}")




# Main script
if __name__ == "__main__":
    course_code = sys.argv[1].upper()
    pdf_path = f"./pdf/{course_code}.pdf"
    output_json = f"units.json"
    output_json_preserveRelationship = f"./course_to_unit/{course_code}.json"

    # Extract unit codes from the PDF
    unit_codes = extract_unit_code(pdf_path)

    # Save or append the unit codes to the JSON file
    save_units_to_json(unit_codes, output_json)
    save_units_to_json(unit_codes, output_json_preserveRelationship)