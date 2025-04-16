# The purpose of this script is to pull information from the each course information.
import sys
import scrapy
from scrapy_splash import SplashRequest
from scrapy.crawler import CrawlerProcess
import subprocess
from datetime import datetime
import re
import json
import unicodedata
import pdfplumber
import requests


class MySpider(scrapy.Spider):
    name = "unit_spider"
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
    }
    def __init__(self, unitLink = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.unitLink = unitLink
    
    def start_requests(self):
        if self.unitLink:
            yield SplashRequest(
                url=self.unitLink,
                callback=self.parse,
                errback=self.handle_error, 
                args={'wait': 5},  # Adjust wait time if needed
            )
        else:
            self.logger.error("No Unit link provided.")
    
    @staticmethod
    def normalize_text(text):
        # Replace smart quotes and other typographic characters with ASCII equivalents
        text = text.replace('’', "'")  # right single quote
        text = text.replace('‘', "'")  # left single quote
        text = text.replace('“', '"')  # left double quote
        text = text.replace('”', '"')  # right double quote
        text = unicodedata.normalize('NFKC', text)  # normalize Unicode
        return text

    def handle_error(self, failure):
        #Log the error and add the unit to not_unit
            self.handle_missing_unit(
        url=failure.value.response.url,
        error_message=f"HTTP error {failure.value.response.status}",
        missing_fields=["unit_code"]
    )
            
    def clean_prerequisites(self, prerequisites):
        if not prerequisites:
            return None

        # Extract all text, including links and plain text
        prerequisites = prerequisites.strip()

        # Remove the word "or" from the prerequisites
        prerequisites = re.sub(r'\bor\b', '', prerequisites, flags=re.IGNORECASE)

        # Normalize whitespace
        prerequisites = re.sub(r'\s+', ' ', prerequisites).strip()

        return prerequisites if prerequisites else None

    def clean_equivalents(self, equivalents):
        if not equivalents:
            return None
        equivalents = equivalents.strip()
        # If contains the generic message, return None
        if "You can't enrol in this unit if you have completed any of these equivalent units" in equivalents:
            return None
        # Remove extra spaces and separators
        equivalents = [e.strip() for e in equivalents.replace(' and ', ',').split(',')]
        # Filter out empty strings and non-course codes
        equivalents = [e for e in equivalents if e and not e.startswith('You')]
        return equivalents if equivalents else None


    def parse(self, response):
        try:
            # Extract unit information  
            unitCode= response.xpath('//dt[contains(text(), "Unit code")]/following-sibling::dd[1]/text()').get()
            faculty= response.xpath('//dt[contains(text(), "Faculty")]/following-sibling::dd[1]/text()').get()
            school= response.xpath('//dt[contains(text(), "School/Discipline")]/following-sibling::dd[1]/text()').get()
            studyArea= response.xpath('//dt[contains(text(), "Study area")]/following-sibling::dd[1]/text()').get()
            creditPoints= response.xpath('//dt[contains(text(), "Credit points")]/following-sibling::dd[1]/text()').get()
            prerequisites_raw = response.xpath('//dt[contains(text(), "Prerequisites")]/following-sibling::dd[1]//text()').getall()
            joined_text = " ".join([text.strip() for text in prerequisites_raw if text.strip()])
            unit_codes = re.findall(r'\b[A-Z]{3}\d{3}\b', joined_text)
            prerequisites = unit_codes if unit_codes else None         
            equivalents= self.clean_equivalents(response.xpath('//dt[contains(text(), "Equivalents")]/following-sibling::dd[1]/text()').get())
            anti_requisites = response.xpath('//dt[contains(text(), "Anti-requisites")]/following-sibling::dd[1]/text()').get()
              # Extract the subject overview content
            overview_selector = response.xpath('//div[@id="subject-offering"]').get()
            print(overview_selector)
            # Debugging step: Print the raw content of the overview section to help identify issues
            overview_content = overview_selector.get()
            self.logger.info(f"Overview Section Content: {overview_content[:500]}")  # Print first 500 characters for debugging

            sections = {}

            # Loop through headings and their corresponding text
            for heading in overview_selector.xpath('.//h4 | .//h5'):
                title = heading.xpath('normalize-space()').get()
                # Get all following siblings until the next heading
                texts = heading.xpath('following-sibling::*')
                content = []
                for elem in texts:
                    if elem.root.tag in ['h4', 'h5']:
                        break  # Stop at the next section heading
                    content.extend(elem.xpath('.//text()').getall())
                
                # Clean up the content
                cleaned_text = ' '.join(t.strip() for t in content if t.strip())
                sections[title] = cleaned_text


            extracted_data = {
                "unitCode": unitCode,
                "faculty": faculty,
                "school": school,
                "studyArea": studyArea,
                "studyArea": studyArea,
                "creditPoints": creditPoints,
                "prerequisites": prerequisites,
                "equivalents": equivalents,
                "anti_requisites": anti_requisites,
                "overview": sections,
                'url': self.unitLink,
                'day_obtained': datetime.now().strftime('%Y-%m-%d'),
            }


            # Save the extracted data to a separate JSON file for each unit_code
            if unitCode:
                output_file = f"./units/{unitCode}.json"
            else:
                output_file = "./units/unknown_unit.json"

            try:
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(extracted_data, f, indent=4, ensure_ascii=False) 
            except Exception as e:
                print(f"Error writing to {output_file}: {e}")


            # Yield the extracted data as output
            yield extracted_data

        except Exception as e:
            self.logger.error(f"Error parsing unit: {str(e)}")
            return {}

        



# Access arguments passed to the script
unit_code = sys.argv[1]  # First argument


unit = re.sub(r"\s+", "-", unit_code).upper()  # Replace spaces with hyphens

unitLink = f"https://www.qut.edu.au/study/unit?unitCode={unit}"
print(unitLink)

# Run the spider with the unit_link argument
process = CrawlerProcess()
process.crawl(MySpider, unitLink=unitLink)
process.start()