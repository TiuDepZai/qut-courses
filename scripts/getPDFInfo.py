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



def download_pdf(self, pdf_url, course_code):
# Download PDF (if any)
    try:
        response = requests.get(pdf_url)
        if response.status_code == 200:
            pdf_filename = f"{course_code}_course_structure.pdf"
            with open(pdf_filename, "wb") as f:
                f.write(response.content)
            self.logger.info(f"PDF downloaded: {pdf_filename}")
        else:
            self.logger.warning(f"Failed to download PDF for {course_code}")
    except requests.RequestException as e:
        self.logger.error(f"Error downloading PDF: {e}")
        
unitcode = ""
id = ""
unit_synposis = f"https://pdf.courses.qut.edu.au/coursepdf/qut_{unitcode}_{id}_dom_cms_unit.pdf"