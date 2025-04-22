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
            print("No PDF URL provided.")

    def parse_pdf(self, response):
        try:
            pdf_filename = "./pdf/temp.pdf"
            os.makedirs(os.path.dirname(pdf_filename), exist_ok=True)
            with open(pdf_filename, "wb") as f:
                f.write(response.body)
            print(f"PDF downloaded: {pdf_filename}")
        except Exception as e:
            print(f"Error saving PDF: {e}")




# ====== Run the spider ======
unitCode = sys.argv[1]  # First argument
id = sys.argv[2]

pdf_url = f"https://pdf.courses.qut.edu.au/coursepdf/qut_{unitCode}_{id}_dom_cms_unit.pdf"

process = CrawlerProcess()
process.crawl(PDFSpider, pdf_url=pdf_url)
process.start()  # Download PDF


