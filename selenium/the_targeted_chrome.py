from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

options = webdriver.ChromeOptions()
options.add_argument("--headless")  # Optional: run without opening a browser window

# Automatically downloads the correct ChromeDriver for your Chrome version
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
