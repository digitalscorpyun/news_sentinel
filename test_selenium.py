from selenium import webdriver
from selenium.webdriver.chrome.service import Service

# Path to ChromeDriver
service = Service("E:/Python Basics/chromedriver/chromedriver-win64/chromedriver.exe")

# Initialize WebDriver
driver = webdriver.Chrome(service=service)

# Open Google and print the page title
driver.get("https://www.google.com")
print("Page Title:", driver.title)

# Close the browser
driver.quit()
