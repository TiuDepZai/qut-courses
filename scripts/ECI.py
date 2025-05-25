# The purpose of this script is to pull information from each course page.
import sys
import scrapy
from scrapy_splash import SplashRequest
from scrapy.crawler import CrawlerProcess
from datetime import datetime
import re
import json
import unicodedata
import os


class MySpider(scrapy.Spider):
    name = "course_spider"
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
    }

    def __init__(self, courseLink=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.courseLink = courseLink

    def start_requests(self):
        if self.courseLink:
            yield SplashRequest(
                url=self.courseLink,
                callback=self.parse,
                errback=self.handle_error,
                args={'wait': 10},  # Adjust wait time if needed
            )
        else:
            self.logger.error("No course link provided.")

    @staticmethod
    def normalize_text(text):
        # Normalize text by replacing special characters and normalizing Unicode

        text = text.replace('’', "'")  # right single quote
        text = text.replace('‘', "'")  # left single quote
        text = text.replace('“', '"')  # left double quote
        text = text.replace('”', '"')  # right double quote
        text = unicodedata.normalize('NFKC', text)  # normalize Unicode
        return text

    def handle_error(self, failure):
        # Handle errors during the request
        print(f"Error occurred: {failure.value.response.status} for URL: {failure.request.url}")
        status_code = failure.value.response.status
        if status_code == 404:
            error_message = "Website not found"
        else:
            error_message = f"HTTP error {status_code}"

        self.handle_missing_course(
            url=failure.value.response.url,
            error_message=error_message,
            missing_fields=["course_name", "course_code"]
        )


    def handle_missing_course(self, url, error_message, missing_fields=None):
        #Handles courses with missing data by logging and saving to `not_courses.json`.
        
        missing_course = {
            "url": url,
            "error": error_message,
        }
        if missing_fields:
            missing_course["missing_fields"] = missing_fields

        try:
            with open("not_courses.json", "r", encoding="utf-8") as f:
                not_courses = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            not_courses = []

        not_courses.append(missing_course)

        with open("not_courses.json", "w", encoding="utf-8") as f:
            json.dump(not_courses, f, indent=4)

        print(f"Missing or invalid course data for URL: {url}")

    def parse(self, response):
        try:
            # Check if the page contains the course-tab-wrapper div
            is_course_page = response.xpath('//*[@id="course-tab-wrapper"]').get() is not None

            if not is_course_page:
                # Handle as an overview page
                self.handle_missing_course(
                    url=response.url,
                    error_message="Overview Page not a course",
                    missing_fields=["ContentPanel"]
                )
                return  # Exit early if it's not a course page

            # Extract course name
            course_name = response.xpath('//span[@data-course-map-key="courseTitle"]/text()').get()
            course_name = course_name.strip() if course_name else None

            # Extract course code
            course_code = response.xpath('//dd[@data-course-map-key="reqTabCourseCode"]/text()').get()
            course_code = course_code.strip() if course_code else None

            # Extract durations (Domestic and International)
            durations = response.xpath('//div[contains(@class, "duration-icon")]//li[@data-course-audience]')
            duration_data = []
            for duration in durations:
                audience = duration.xpath('./@data-course-audience').get()  # DOM or INT
                text = duration.xpath('./text()').get().strip()  # Duration text
                duration_data.append({'audience': audience, 'duration': text})

            # Extract delivery location
            delivery_location = response.xpath('//div[contains(@class, "col-sm-10")]//b[contains(text(), "Delivery")]/following-sibling::ul/li/text()').get()

            # Extract ATAR/Selection Rank
            atar_rank = response.xpath('//dd[contains(@class, "rank inverted")]/text()').get()

            # Extract QTAC Code
            qtac_code = response.xpath('//b[@data-course-audience="DOM" and contains(text(), "QTAC code")]/following-sibling::ul/li/text()').get()

            # Extract CRICOS Code
            cricos_code = response.xpath('//b[@data-course-audience="INT" and contains(text(), "CRICOS")]/following-sibling::ul/li/text()').get()

            # Extract highlights
            highlights = response.xpath('//div[contains(@class, "container course-highlights") and @data-course-audience="DOM"]//ul/li/text()').getall()
            cleaned_highlights = [MySpider.normalize_text(highlight.strip()) for highlight in highlights if highlight and highlight.strip()]

            # Extract CSP fee
            csp_fee = response.xpath('//div[contains(@class, "box-content")]/p[contains(text(), "CSP")]/text()').re_first(r'CSP \$[\d,]+ per year full-time')

            # Extract all sections dynamically
            panel = response.xpath('//div[contains(@class, "panel-content row")]')
            dynamic_sections = {}

            for section in panel.xpath('.//div[contains(@class, "course-detail-item")]'):
                audience = section.xpath('./@data-course-audience').get()  # DOM or INT
                if 'DOM' not in audience:
                    continue  # Skip if it's not for DOM

                # Extract title
                title = section.xpath('.//h3/text()').get()
                title = title.strip() if title else "Untitled Section"

                # Extract all text including inside <a> tags
                raw_texts = section.xpath('.//p//text()').getall()
                content = [MySpider.normalize_text(text.strip()) for text in raw_texts if text.strip()]

                dynamic_sections[title] = content

            # Extract possible careers
            possible_careers = response.xpath('//div[@data-course-map-key="careerOutcomesList"]//ul/li/text()').getall()
            possible_careers = [career.strip() for career in possible_careers if career.strip()]

            if possible_careers:
                dynamic_sections["Possible Careers"] = possible_careers

            # Extract JSON-LD and get courseCode + identifier
            json_ld = response.xpath('//script[@type="application/ld+json"]/text()').get()
            identifier = json.loads(json_ld).get('identifier', None) if json_ld else None

            # Build the extracted data dictionary
            extracted_data = {
                "course_name": course_name,
                "course_code": course_code,
                "identifier": identifier,
                "durations": duration_data,
                "delivery_location": delivery_location,
                "atar_rank": atar_rank,
                "csp_cost": csp_fee,
                "qtac_code": qtac_code,
                "cricos_code": cricos_code,
                "highlights": cleaned_highlights,
                "what_to_expect-careers_and_outcome": dynamic_sections,
                'source': self.courseLink,
                'day_obtained': datetime.now().strftime('%Y-%m-%d'),
            }

            # Save the extracted data to a separate JSON file for each course
            if course_code:
                output_file = f"./courses/{course_code}.json"
            else:
                output_file = f"./courses/{course_name.replace(' ', '_').lower()}.json"

            # Write extracted data into a JSON object
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(extracted_data, f, indent=4, ensure_ascii=False)

            # Yield the extracted data as output
            yield extracted_data
            print(f"Data extracted and saved to {output_file}")

        except Exception as e:
            # Handle unexpected errors
            self.handle_missing_course(response.url, str(e))
            return  # Exit early

if __name__ == "__main__":
    # Access arguments passed to the script
    course_code = sys.argv[1]  # First argument
    course_title = sys.argv[2]  # Second argument

    # Construct the course_link
    course_title = re.sub(r"\s+", "-", course_title).lower()  # Replace spaces with hyphens
    course_title = re.sub(r"/", "-", course_title)  # Replace slashes with hyphens
    course_title = re.sub(r"-{2,}", "-", course_title)  # Replace multiple consecutive hyphens with a single hyphen
    course_title = re.sub(r"[()]", "", course_title)  # Remove parentheses
    course_title = course_title.strip("-")  # Remove leading or trailing hyphens

    courseLink = f"https://www.qut.edu.au/courses/{course_title}"
    
    # Ensure the output directory exists
    output_dir = "./courses/"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")


    # Run the spider with the course_link argument
    process = CrawlerProcess()
    process.crawl(MySpider, courseLink=courseLink)
    process.start()