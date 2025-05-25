import fitz  # PyMuPDF
import json
import re
import sys
import os
from datetime import datetime

def extract_unit_code(pdf_path):
    #Extracts unique unit codes from tables in the PDF.

    # Open the PDF file
    doc = fitz.open(pdf_path)

    # Regular expression to match unit codes (e.g., ABB123)
    unit_code_pattern = re.compile(r'^[A-Z]{3}\d{3}$')

    unique_unit_codes = set()  # To track unique unit codes globally

    # Iterate through each page in the PDF
    for page in doc:
        tables = page.find_tables()
        # If no tables are found, skip to the next page
        if not tables:
            continue
        # Iterate through each table found on the page and extract data according to the pattern
        for table in tables:
            table_data = table.extract()
            for row in table_data:
                cleaned_row = [str(cell).strip() if cell else "" for cell in row]
                if cleaned_row[0] and unit_code_pattern.match(cleaned_row[0]):
                    unit_code = cleaned_row[0]
                    unique_unit_codes.add(unit_code)  # Add only the unit code

    doc.close()
    return list(unique_unit_codes)  # Convert the set to a list

def save_units_to_json(course_code, new_unit_codes, course_id, output_json, preserve_relationship=False):
    #Appends new unit codes to an existing JSON file or creates a new one if it doesn't exist.
    #Stores the unit codes as a simple list of strings.
    
    # Load existing data if the file exists
    if os.path.exists(output_json):
        with open(output_json, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
            existing_unit_codes = set(
                entry["unitCode"] if isinstance(entry, dict) else entry
                for entry in existing_data.get("unitCodes", []))
    else:
        existing_data = {}
        existing_unit_codes = set()

    # Add new unit codes to the existing set
    updated_unit_codes = existing_unit_codes.union(new_unit_codes)
    
    # Build the JSON structure
    if preserve_relationship:
        # Only retain 'source' and 'day_obtained'
        updated_data = {
            "source": f"https://pdf.courses.qut.edu.au/coursepdf/qut_{course_code}_{course_id}_dom_cms_unit.pdf",
            "day_obtained": datetime.now().strftime('%Y-%m-%d'),

        }
    else:
        # Save the full data with unit codes
        updated_data = {
            "unitCodes": sorted(updated_unit_codes)
        }

    # Save the updated data back to the JSON file
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(updated_data, f, indent=4)

    print(f"Data extracted and saved to {output_json}")

    




# Main script
if __name__ == "__main__":
    course_code = sys.argv[1].upper()
    course_id = sys.argv[2]

    pdf_path = f"./pdf/{course_code}.pdf"
    output_json = f"units.json"
    output_json_preserveRelationship = f"./course_to_unit/{course_code}.json"

    # Extract unit codes from the PDF
    unit_codes = extract_unit_code(pdf_path)

    # Save or append the unit codes to the JSON file
    save_units_to_json(course_code, unit_codes, course_id, output_json)
    save_units_to_json(course_code, unit_codes, course_id, output_json_preserveRelationship, preserve_relationship=True)