import sys
import scrapy
from scrapy.crawler import CrawlerProcess
import logging
import fitz  # PyMuPDF
import re
import json
import os
import traceback
from pathlib import Path

# Silence pdfminer debug logging
logging.getLogger("pdfminer").setLevel(logging.WARNING)
2

def fix_split_codes(text):
    """
    Fixes unit codes that might be split across lines.
    For example, "ABB\n101" becomes "ABB101".
    """
    # Replace newlines between letters and numbers in unit codes
    fixed = re.sub(r'([A-Z]{3})\s*\n\s*(\d{3})', r'\1\2', text)
    return fixed

def extract_unit_codes_grouped(pdf_path):
    """
    Extracts unit codes grouped by semester and by section from the given PDF file using PyMuPDF.
    Specifically designed for QUT course PDFs with complex layouts.
    """
    try:
        # Open the PDF with PyMuPDF
        doc = fitz.open(pdf_path)
        
        # Limit to first two pages
        pages_to_process = min(2, len(doc))
        
        # Extract text from each page
        page_texts = []
        
        for page_num in range(pages_to_process):
            page = doc[page_num]
            print(f"\n--- Page {page_num+1} ---\n")
            
            # Extract text with layout preservation
            text = page.get_text("text")
            if text:
                page_texts.append(text)
        
        # Close the document
        doc.close()
        
        # Combine all page texts
        full_text = '\n'.join(page_texts)
        
        # Fix split unit codes
        fixed_text = fix_split_codes(full_text)
        
        # Extract course code
        course_code = None
        course_code_pattern = r'Course code:\s*([A-Z0-9]+)'
        course_code_match = re.search(course_code_pattern, fixed_text)
        if course_code_match:
            course_code = course_code_match.group(1)
            print(f"Found course code: {course_code}")
        
        # If no course code found, try to extract it from the filename
        if not course_code:
            filename = os.path.basename(pdf_path)
            course_code_match = re.search(r'qut_([A-Z0-9]+)_', filename)
            if course_code_match:
                course_code = course_code_match.group(1)
                print(f"Extracted course code from filename: {course_code}")
        
        # If still no course code, use a default
        if not course_code:
            course_code = "UNKNOWN"
            print("No course code found, using default: UNKNOWN")
        
        # Extract entry times and study modes
        entry_times = []
        study_modes = []
        
        # Look for entry time patterns (e.g., "February entry", "July entry")
        entry_time_pattern = r'([A-Za-z]+ entry)'
        entry_time_matches = re.findall(entry_time_pattern, fixed_text)
        if entry_time_matches:
            entry_times = list(set(entry_time_matches))
            print(f"Found entry times: {entry_times}")
        
        # Look for study mode patterns (e.g., "Full Time", "Part Time")
        study_mode_pattern = r'(Full Time|Part Time)'
        study_mode_matches = re.findall(study_mode_pattern, fixed_text)
        if study_mode_matches:
            study_modes = list(set(study_mode_matches))
            print(f"Found study modes: {study_modes}")
        
        # If no entry times or study modes found, use defaults
        if not entry_times:
            entry_times = ["February entry", "July entry"]
        if not study_modes:
            study_modes = ["Full Time", "Part Time"]
        
        # Extract semester information and unit codes
        # This is a more direct approach for QUT course PDFs
        semester_units = {}
        
        # Define the semester pattern
        semester_pattern = r'Year (\d), Semester (\d)'
        
        # Find all semester headers
        semester_matches = list(re.finditer(semester_pattern, fixed_text))
        
        if semester_matches:
            print(f"Found {len(semester_matches)} semester headers")
            
            # Create a list of semester positions with their names
            semester_positions = []
            for match in semester_matches:
                year = match.group(1)
                semester = match.group(2)
                semester_key = f"Year {year}, Semester {semester}"
                semester_positions.append((match.start(), semester_key))
                print(f"Semester header: {semester_key} at position {match.start()}")
            
            # Sort by position to ensure correct order
            semester_positions.sort(key=lambda x: x[0])
            
            # Add a virtual end position for the last semester
            semester_positions.append((len(fixed_text), None))
            
            # Process each semester
            for i in range(len(semester_positions) - 1):
                start_pos, semester = semester_positions[i]
                end_pos = semester_positions[i + 1][0]
                
                # Extract the text for this semester
                semester_text = fixed_text[start_pos:end_pos]
                
                # Extract unit codes for this semester
                unit_codes = re.findall(r'\b[A-Z]{3}\d{3}\b', semester_text)
                
                # Remove duplicates and sort
                if unit_codes:
                    # Create a new list for this semester
                    semester_units[semester] = sorted(set(unit_codes))
                    print(f"Found {len(unit_codes)} unit codes for {semester}")
        
        # Extract section-based unit organization
        sections = {}
        
        # Look for section headers (e.g., "Planning", "Design", etc.)
        # This pattern looks for lines that are all caps or have specific formatting
        section_pattern = r'^([A-Z][A-Za-z\s]+)$'
        section_matches = list(re.finditer(section_pattern, fixed_text, re.MULTILINE))
        
        if section_matches:
            print(f"Found {len(section_matches)} potential section headers")
            
            # Create a list of section positions with their names
            section_positions = []
            for match in section_matches:
                section_name = match.group(1).strip()
                # Skip common headers that aren't sections
                if section_name.lower() in ["course code", "course title", "duration", "atar", "credit points", "start months", "contact"]:
                    continue
                section_positions.append((match.start(), section_name))
                print(f"Section header: {section_name} at position {match.start()}")
            
            # Sort by position to ensure correct order
            section_positions.sort(key=lambda x: x[0])
            
            # Add a virtual end position for the last section
            section_positions.append((len(fixed_text), None))
            
            # Process each section
            for i in range(len(section_positions) - 1):
                start_pos, section_name = section_positions[i]
                end_pos = section_positions[i + 1][0]
                
                # Extract the text for this section
                section_text = fixed_text[start_pos:end_pos]
                
                # Extract unit codes and titles for this section
                unit_info = []
                unit_matches = re.finditer(r'([A-Z]{3}\d{3})\s+([^\n]+)', section_text)
                for unit_match in unit_matches:
                    unit_code = unit_match.group(1)
                    unit_title = unit_match.group(2).strip()
                    unit_info.append({"code": unit_code, "title": unit_title})
                
                if unit_info:
                    sections[section_name] = unit_info
                    print(f"Found {len(unit_info)} units in section {section_name}")
        
        # If no semester information found, try a different approach
        if not semester_units and not sections:
            print("No semester or section information found. Trying alternative approach...")
            return extract_units_alternative(pdf_path)
        
        # Create a structured JSON format with course code at the top level
        result = {}
        
        # Create entries for this course
        course_entries = []
        
        # Create a combination for each entry time and study mode
        for entry_time in entry_times:
            for study_mode in study_modes:
                # Extract the month from the entry time (e.g., "February" from "February entry")
                month = entry_time.split()[0]
                
                # Create a new entry for this combination
                entry = {
                    "entry_time": month,
                    "mode": study_mode,
                    "course_semesters": {}
                }
                
                # Add semester information
                for semester, codes in semester_units.items():
                    # Convert semester format to match your desired output
                    semester_key = f"year {semester.split(', ')[0].split()[1]} semester {semester.split(', ')[1].split()[1]}"
                    entry["course_semesters"][semester_key] = codes
                
                course_entries.append(entry)
        
        # Add the entries to the result
        result[course_code] = course_entries
        
        # Add sections to the result
        if sections:
            result["sections"] = sections
        
        return result

    except Exception as e:
        print(f"Error extracting unit codes: {e}")
        traceback.print_exc()
        return {}

def extract_units_alternative(pdf_path):
    """
    Alternative approach to extract unit codes when the main method fails.
    """
    try:
        # Open the PDF with PyMuPDF
        doc = fitz.open(pdf_path)
        
        # Extract all unit codes from the first two pages
        unit_codes = set()
        for page_num in range(min(2, len(doc))):
            page = doc[page_num]
            text = page.get_text("text")
            codes = re.findall(r'\b[A-Z]{3}\d{3}\b', text)
            unit_codes.update(codes)
        
        # Close the document
        doc.close()
        
        return {"All Units": sorted(unit_codes)}
    
    except Exception as e:
        print(f"Error in alternative extraction: {e}")
        traceback.print_exc()
        return {"All Units": []}

def extract_course_guide_info(pdf_path):
    """
    Extracts course guide information (study mode and entry times) from the PDF.
    Handles multi-column layout by using PyMuPDF's block-based extraction.
    """
    try:
        # Open the PDF with PyMuPDF
        doc = fitz.open(pdf_path)
        
        # Dictionary to store course guide information
        course_guides = {}
        
        # Process each page
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # Get blocks of text (this helps with column layout)
            blocks = page.get_text("blocks")
            
            # Sort blocks by vertical position (y0) to maintain reading order
            blocks.sort(key=lambda b: b[1])  # b[1] is the y0 coordinate
            
            # Process each block
            for block in blocks:
                text = block[4]  # block[4] contains the text content
                
                # Look for study mode information
                study_mode_match = re.search(r'(Full Time|Part Time)', text)
                if study_mode_match:
                    mode = study_mode_match.group(1)
                    if mode not in course_guides:
                        course_guides[mode] = {"entry_times": set()}
                
                # Look for entry time information
                entry_time_match = re.search(r'(February|July)\s+entry', text)
                if entry_time_match:
                    entry_time = entry_time_match.group(1)
                    # Add entry time to all existing modes
                    for mode in course_guides:
                        course_guides[mode]["entry_times"].add(entry_time)
        
        # Close the document
        doc.close()
        
        # Convert sets to lists for JSON serialization
        for mode in course_guides:
            course_guides[mode]["entry_times"] = sorted(list(course_guides[mode]["entry_times"]))
        
        return course_guides

    except Exception as e:
        print(f"Error extracting course guide information: {e}")
        traceback.print_exc()
        return {}

def process_pdf_files():
    """
    Process all PDF files in the current directory and save results to JSON files.
    """
    # Get the current directory
    current_dir = os.getcwd()
    
    # Find all PDF files in the current directory
    pdf_files = [f for f in os.listdir(current_dir) if f.endswith('.pdf')]
    
    if not pdf_files:
        print("No PDF files found in the current directory.")
        return
    
    # Process each PDF file
    for pdf_file in pdf_files:
        pdf_path = os.path.join(current_dir, pdf_file)
        print(f"Processing {pdf_file}...")
        
        # Extract course guide information
        course_guides = extract_course_guide_info(pdf_path)
        
        # Save the results to a JSON file
        output_file = os.path.splitext(pdf_file)[0] + '_course_guides.json'
        with open(output_file, 'w') as f:
            json.dump(course_guides, f, indent=4)
        
        print(f"Results saved to {output_file}")

if __name__ == "__main__":
    # Check if a URL was provided as a command-line argument
    if len(sys.argv) > 1:
        url = sys.argv[1]
        pdf_path = download_pdf(url)
        if pdf_path:
            course_guides = extract_course_guide_info(pdf_path)
            print(json.dumps(course_guides, indent=4))
    else:
        # Process all PDF files in the current directory
        process_pdf_files()

# ====== Run the spider ======
unitCode = sys.argv[1]  # First argument
id = sys.argv[2]

pdf_url = f"https://pdf.courses.qut.edu.au/coursepdf/qut_{unitCode}_{id}_dom_cms_unit.pdf"

process = CrawlerProcess()
process.crawl(PDFSpider, pdf_url=pdf_url)
process.start()  # Download PDF

# After spider finishes, extract the codes
extracted_units = extract_unit_codes_grouped("./pdf/temp_pdf.pdf")

# Write all units to all_units.json
all_units_path = "./pdf/all_units.json"
os.makedirs(os.path.dirname(all_units_path), exist_ok=True)

with open(all_units_path, "w", encoding="utf-8") as f:
    json.dump(extracted_units, f, indent=4)

print(f"All units saved to: {all_units_path}")

# Write course-to-unit relationship to course_unit_relationships.json
relationship_path = "./pdf/course_unit_relationships.json"
os.makedirs(os.path.dirname(relationship_path), exist_ok=True)

# Load existing data if the file exists
if os.path.exists(relationship_path):
    with open(relationship_path, "r", encoding="utf-8") as f:
        try:
            existing_data = json.load(f)
        except json.JSONDecodeError:
            existing_data = {}
else:
    existing_data = {}

# Update the dictionary with the new course and its units
existing_data[unitCode] = extracted_units

# Write the updated data back
with open(relationship_path, "w", encoding="utf-8") as f:
    json.dump(existing_data, f, indent=4)

print(f"Course-unit relationships saved to: {relationship_path}")

