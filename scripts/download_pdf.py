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

class PDFSpider(scrapy.Spider):
    name = "pdf_spider"
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
    }
    # Initialize the spider with the PDF URL and course code
    def __init__(self, pdf_url=None, courseCode = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pdf_url = pdf_url
        self.courseCode = courseCode

    # Start the spider by making a request to the PDF URL
    def start_requests(self):
        if self.pdf_url:
            yield scrapy.Request(
                url=self.pdf_url,
                callback=self.parse_pdf
            )
        else:
            print("No PDF URL provided.")

    # Write the PDF content to a pdf file
    def parse_pdf(self, response):
        try:
            pdf_filename = f"./pdf/{self.courseCode}.pdf"
            os.makedirs(os.path.dirname(pdf_filename), exist_ok=True)
            with open(pdf_filename, "wb") as f:
                f.write(response.body)
            print(f"PDF downloaded: {pdf_filename}")
        except Exception as e:
            print(f"Error saving PDF: {e}")



if __name__ == "__main__":

   # Ensure the output directory exists
    output_dir = "./pdf/"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")

    # Pull the course code and ID from command line arguments
    courseCode = sys.argv[1]  # First argument
    id = sys.argv[2]

    # Construct the PDF URL
    pdf_url = f"https://pdf.courses.qut.edu.au/coursepdf/qut_{courseCode}_{id}_dom_cms_unit.pdf"

    # Run the spider
    process = CrawlerProcess()
    process.crawl(PDFSpider, pdf_url=pdf_url, courseCode = courseCode)
    process.start()  # Download PDF


