# The purpose of this script is to pull information from the https://www.qut.edu.au/about/governance-and-policy/handbooks-course-lists-and-award-abbreviations/active-courses-list 
# page and save it to a file.

import scrapy
from scrapy_splash import SplashRequest
from scrapy.crawler import CrawlerProcess
from scrapy.http import HtmlResponse
import os
import json 
from datetime import datetime

class CourseSpider(scrapy.Spider):
    name = 'courses'
    start_urls = ['https://www.qut.edu.au/about/governance-and-policy/handbooks-course-lists-and-award-abbreviations/active-courses-list']

    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
    }

    def start_requests(self):
        yield SplashRequest(
            url=self.start_urls[0],
            callback=self.parse,
            args={'wait': 2},  
        )

    def parse(self, response):

            # Extract all course titles from <h3> tags
            course_titles = response.css('h3::text').getall()

            # Prepare the list of courses
            courses = []

            # Yield each course title with separated fields
            for title in course_titles:
                # Split the title into courseCode and course_title
                parts = title.strip().split(" ", 1)
                if len(parts) == 2:
                    course_code, course_name = parts
                else:
                    course_code, course_name = parts[0], ""

                courses.append({
                    'courseCode': course_code,
                    'course_title': course_name,
                })

            # Build the final output structure
            extracted_data = {
                'source': self.start_urls[0],
                'day_obtained': datetime.now().strftime('%Y-%m-%d'),
                'list_of_courses': courses,
            }

            # Save the extracted data to a JSON file
            output_file = 'courses.json'
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(extracted_data, f, indent=4)

            # Yield the extracted data as output
            yield extracted_data

# Function to run the spider
def run_spider():
    output_file = 'courses.json'

    # Check if courses.json exists and delete it
    if os.path.exists(output_file):
        os.remove(output_file)
        print(f"{output_file} has been deleted.")

    # Set up the crawler process with settings
    process = CrawlerProcess(settings={
        'FEED_FORMAT': 'json', 
    })
    process.crawl(CourseSpider)  # Start crawling with the CourseSpider
    process.start()  # Start the crawling process
    
if __name__ == "__main__":
    run_spider()