#QUT Course Scraper 🚀  
##Overview  
This project automatically pulls course and unit data from QUT using Scrapy and stores it in MongoDB. The setup includes all necessary dependencies for quick installation.  

##1. Install Python Windows  
1. Download Python from the official site: [Python Downloads](https://www.python.org/downloads/)
2. Run the installer and check the box for "Add Python to PATH" before installing.
3. Verify installation:  
python --version

##2. Insatll Python Linux/MacOS  
Most Linux and MacOS will come with python pre-installed.   
To Check:  
python3 --version  

###Debian/Ubuntu  
sudo apt update  
sudo apt install python3 python3-pip  

###MacOS
brew install python

###Verify Installation:
python3 --version

##Setup Instructions
1. Clone the Repository
git clone https://github.com/YOUR_USERNAME/qut-course-scraper.git
cd qut-course-scraper

2. Install Dependencies

Windows
pip install -r requirements.txt

Linux/MacOS
python3 -m pip install -r requirements.txt

3. Running the Scrapy Crawler
scrapy crawl qut_courses

4. MongoDB Integration
Windows
Download MongoDB
[MongoDB Downloads](https://www.mongodb.com/try/download/community)
Install and start MongoDB
net start MondoDB

Linux/macOS
Debian/Ubuntu
sudo apt update
sudo apt install -y mongodb
sudo systemctl start mongod

macOS (Homebrew users)
brew tap mongodb/brew
brew install mongodb-community@6.0
brew services start mongodb-community@6.0

Check MongoDB status:
mongod --version

Contributing
Feel free to submit issues or pull requests to improve this scraper.

License
This project is open-source and available under the MIT License.
