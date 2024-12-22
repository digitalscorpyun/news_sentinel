import requests
import feedparser
import csv
import logging
import os
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import json
from requests.exceptions import RequestException

# --- Load Configuration ---
with open("config.json", "r") as config_file:
    CONFIG = json.load(config_file)

# --- Logging Configuration ---
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = f"news_sentinel_log_{timestamp}.log"
logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
logging.getLogger().addHandler(console_handler)

# --- Global Variables ---
KEYWORDS = CONFIG.get("KEYWORDS", [])
RSS_FEEDS = CONFIG.get("RSS_FEEDS", {})
WEBSITES = CONFIG.get("WEBSITES", {})

# --- Helper Functions ---
def fetch_rss_feed(url, retries=3, backoff_factor=2):
    """Fetch articles from an RSS feed with retries."""
    for attempt in range(retries):
        try:
            feed = feedparser.parse(url)
            if not feed.bozo:
                return feed.entries
        except Exception as e:
            logging.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
            time.sleep(backoff_factor ** attempt)  # Exponential backoff
    logging.error(f"Failed to fetch RSS feed after {retries} attempts: {url}")
    return []

def initialize_webdriver():
    """Initialize Selenium WebDriver for dynamic content scraping."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_service = ChromeService(executable_path=ChromeDriverManager().install())
    return webdriver.Chrome(service=chrome_service, options=chrome_options)

def fetch_dynamic_content(url, source_name, retries=3):
    """Fetch articles from dynamically loaded websites using Selenium."""
    for attempt in range(retries):
        try:
            driver = initialize_webdriver()
            driver.get(url)
            time.sleep(5)  # Allow time for dynamic content to load
            articles = driver.find_elements(By.TAG_NAME, "a")
            results = []
            for article in articles:
                title = article.text.strip()
                link = article.get_attribute("href")
                if title and link and any(keyword.lower() in title.lower() for keyword in KEYWORDS):
                    results.append({"title": title, "link": link, "source": source_name})
            driver.quit()
            return results
        except Exception as e:
            logging.error(f"Selenium scraping error for {url}: {e}")
            time.sleep(2 ** attempt)  # Exponential backoff
    logging.error(f"Failed to scrape dynamic content after {retries} attempts: {url}")
    return []

def save_to_csv(articles, filename):
    """Save articles to a CSV file."""
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Source", "Title", "Link", "Keywords Used"])
        for article in articles:
            source = article.get("source", "").strip()
            title = article.get("title", "").strip()
            link = f'=HYPERLINK("{article.get("link", "")}", "Link")'
            keywords = ", ".join(article.get("keywords", []))
            writer.writerow([source, title, link, keywords])

def filter_articles_by_keywords(articles, keywords):
    """Filter articles based on keywords."""
    filtered_articles = []
    for article in articles:
        title = article.get("title", "").lower()
        matching_keywords = [keyword for keyword in keywords if keyword.lower() in title]
        if matching_keywords:
            article["keywords"] = matching_keywords
            filtered_articles.append(article)
    return filtered_articles

# --- Main Script ---
def main():
    logging.info("News Sentinel started.")
    all_articles = []
    filtered_articles = []

    # --- Fetch articles from RSS feeds ---
    for source_name, url in RSS_FEEDS.items():
        logging.info(f"Fetching articles from RSS feed: {source_name}")
        articles = fetch_rss_feed(url)
        if articles:
            for entry in articles:
                all_articles.append({
                    "title": entry.get("title", "").strip(),
                    "link": entry.get("link", "").strip(),
                    "source": source_name
                })
        else:
            logging.warning(f"No articles fetched from RSS feed: {source_name}")

    # --- Fetch articles from dynamic websites ---
    for source_name, url in WEBSITES.items():
        if source_name not in RSS_FEEDS:  # Avoid duplicating RSS sources
            logging.info(f"Scraping articles from dynamic site: {source_name}")
            articles = fetch_dynamic_content(url, source_name)
            all_articles.extend(articles)

    # --- Filter articles by keywords ---
    filtered_articles = filter_articles_by_keywords(all_articles, KEYWORDS)
    logging.info(f"Filtered {len(filtered_articles)} articles matching keywords.")

    # --- Ensure minimum 200 articles ---
    if len(filtered_articles) < 200:
        logging.warning("Fewer than 200 articles found. Adding unfiltered articles to meet the quota.")
        additional_articles = [article for article in all_articles if article not in filtered_articles]
        filtered_articles += additional_articles[:200 - len(filtered_articles)]
    logging.info(f"Total articles after fallback: {len(filtered_articles)}")

    # --- Save to CSV ---
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"news_{timestamp}.csv"
    save_to_csv(filtered_articles, output_file)
    logging.info(f"Saved {len(filtered_articles)} articles to {output_file}")

if __name__ == "__main__":
    main()
