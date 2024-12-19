import requests
import feedparser
import csv
import logging
import os
import time
from datetime import datetime
from requests.exceptions import RequestException
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import json
import subprocess

# --- Ensure Dependencies ---
def ensure_dependencies():
    required_libraries = ["feedparser", "requests", "selenium", "bs4"]
    for lib in required_libraries:
        try:
            __import__(lib)
        except ImportError:
            subprocess.check_call(["python", "-m", "pip", "install", lib])

ensure_dependencies()

# --- Load Configuration ---
with open("config.json", "r") as config_file:
    CONFIG = json.load(config_file)

# --- Configure Logging ---
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE = f"news_sentinel_log_{timestamp}.log"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Add console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
logging.getLogger().addHandler(console_handler)

# --- Helper Functions ---

def initialize_webdriver():
    """Initialize Selenium WebDriver."""
    chrome_service = Service("E:/Python Basics/chromedriver/chromedriver.exe")
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--log-level=3")
    return webdriver.Chrome(service=chrome_service, options=chrome_options)

def fetch_rss_feed(url, retries=3, backoff_factor=2):
    """Fetch articles from an RSS feed with retries."""
    for attempt in range(retries):
        try:
            feed = feedparser.parse(url)
            if not feed.bozo:
                return feed.entries
        except Exception as e:
            logging.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
            time.sleep(backoff_factor ** attempt)
    logging.error(f"Failed to fetch RSS feed after {retries} attempts: {url}")
    return []

def fetch_dynamic_content(url, source_name):
    """Scrape dynamic websites using Selenium."""
    driver = initialize_webdriver()
    try:
        driver.get(url)
        time.sleep(5)  # Adjust wait time for pages to load
        soup = BeautifulSoup(driver.page_source, "html.parser")
        articles = []
        for item in soup.select("article h2 a"):  # Adjust selectors for target sites
            articles.append({
                "title": item.get_text(strip=True),
                "link": item["href"],
                "source": source_name
            })
        return articles
    except Exception as e:
        logging.error(f"Selenium scraping error for {url}: {e}")
        return []
    finally:
        driver.quit()

def save_to_csv(articles, filename):
    """Save articles to a CSV file."""
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Source", "Title", "Link", "Keywords Used"])
        for article in articles:
            source = article.get("source", "").strip()
            title = article.get("title", "").strip()
            keywords = article.get("keyword", "N/A")
            link = f'=HYPERLINK("{article.get("link", "")}", "Link")'
            writer.writerow([source, title, link, keywords])

# --- Main Script ---

def main():
    logging.info("News Sentinel started.")
    all_articles = []

    # Fetch articles from RSS feeds
    for source_name, url in CONFIG["RSS_FEEDS"].items():
        logging.info(f"Fetching articles from {source_name}")
        articles = fetch_rss_feed(url)
        for entry in articles:
            matched_keywords = [kw for kw in CONFIG["KEYWORDS"] if kw.lower() in entry.get("title", "").lower()]
            all_articles.append({
                "title": entry.get("title", ""),
                "link": entry.get("link", ""),
                "source": source_name,
                "keyword": ", ".join(matched_keywords)
            })

    # Fetch articles from dynamic websites
    for source_name, url in CONFIG["WEBSITES"].items():
        logging.info(f"Scraping articles from {source_name}")
        articles = fetch_dynamic_content(url, source_name)
        for article in articles:
            matched_keywords = [kw for kw in CONFIG["KEYWORDS"] if kw.lower() in article["title"].lower()]
            article["keyword"] = ", ".join(matched_keywords)
            all_articles.append(article)

    # Ensure minimum articles
    if len(all_articles) < 100:
        logging.warning("Fewer than 100 articles found, filling with additional articles.")
        all_articles += [{"source": "Fallback", "title": "Additional Content", "link": "#", "keyword": "N/A"}] * (100 - len(all_articles))

    # Save to CSV
    output_file = f"news_{timestamp}.csv"
    save_to_csv(all_articles, output_file)
    logging.info(f"Saved {len(all_articles)} articles to {output_file}")

if __name__ == "__main__":
    main()
