import sys
import scrapy
from scrapy.crawler import CrawlerProcess
import logging
import pdfplumber
import re
import json
import os
import traceback

# Silence pdfminer debug logging
logging.getLogger("pdfminer").setLevel(logging.WARNING)

class PDFSpider(scrapy.Spider):
    name = "pdf_spider"
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
    }

    def __init__(self, pdf_url=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pdf_url = pdf_url

    def start_requests(self):
        if self.pdf_url:
            yield scrapy.Request(
                url=self.pdf_url,
                callback=self.parse_pdf
            )
        else:
            self.logger.error("No PDF URL provided.")

    def parse_pdf(self, response):
        try:
            pdf_filename = "./pdf/temp_pdf.pdf"
            os.makedirs(os.path.dirname(pdf_filename), exist_ok=True)
            with open(pdf_filename, "wb") as f:
                f.write(response.body)
            self.logger.info(f"PDF downloaded: {pdf_filename}")
        except Exception as e:
            self.logger.error(f"Error saving PDF: {e}")

def fix_split_codes(text):
    # Fix unit codes like CSB1\n11 -> CSB111
    text = re.sub(r'([A-Z]{3})\s*\n*\s*(\d)\s*\n*\s*(\d{2})', r'\1\2\3', text)
    return text

def extract_unit_codes_grouped(pdf_path):
    """
    Extracts unit codes grouped by semester from the given PDF file using pdfplumber.
    Preserves semester information for all semesters.
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # Extract text from each page
            page_texts = []
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    page_texts.append(text)
            
            # Combine all page texts
            full_text = '\n'.join(page_texts)
            
            # Fix split unit codes
            fixed_text = fix_split_codes(full_text)
            
            # Find all semester headers with their positions
            semester_pattern = r'(Year \d, Semester \d \(\w+\))'
            semester_matches = list(re.finditer(semester_pattern, fixed_text))
            
            # If no semester headers found, return all unit codes
            if not semester_matches:
                print("No semester headers found in the PDF")
                unit_codes = re.findall(r'\b[A-Z]{3}\d{3}\b', fixed_text)
                return {"All Units": sorted(set(unit_codes))}
            
            print(f"Found {len(semester_matches)} semester headers")
            
            # Process each semester section
            semester_units = {}
            
            # Add a virtual end position for the last semester
            semester_positions = [(match.start(), match.group(1)) for match in semester_matches]
            semester_positions.append((len(fixed_text), None))  # Add end position
            
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
                    semester_units[semester] = sorted(set(unit_codes))
                    print(f"Found {len(unit_codes)} unit codes for {semester}")
            
            # If we still don't have any semesters with units, try a different approach
            if not semester_units:
                print("No units found for any semester. Trying alternative approach...")
                return extract_units_alternative(pdf_path)
            
            return semester_units

    except Exception as e:
        print(f"Error extracting unit codes: {e}")
        traceback.print_exc()
        return {}

def extract_units_alternative(pdf_path):
    """
    Alternative approach to extract unit codes when semester headers are not found.
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            all_unit_codes = set()
            
            # Extract all unit codes from the PDF
            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue
                    
                fixed_text = fix_split_codes(text)
                unit_codes = re.findall(r'\b[A-Z]{3}\d{3}\b', fixed_text)
                all_unit_codes.update(unit_codes)
            
            # If unit codes found, create a simple structure
            if all_unit_codes:
                return {"All Units": sorted(list(all_unit_codes))}
            else:
                return {}
                
    except Exception as e:
        print(f"Error in alternative extraction: {e}")
        return {}

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

