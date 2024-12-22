import requests
import csv
import logging
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import json

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
KEYWORDS = CONFIG.get("keywords", [])
WEBSITES = CONFIG.get("websites", {})

# --- Helper Functions ---
def initialize_webdriver():
    """Initialize Selenium WebDriver for dynamic content scraping."""
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--disable-gpu")  # Disable GPU hardware acceleration
        chrome_options.add_argument("--no-sandbox")  # Disable sandbox (use with caution)
        chrome_options.add_argument("--disable-dev-shm-usage")  # Helps with memory issues in headless mode
        chrome_options.add_argument("--disable-extensions")  # Disable Chrome extensions
        chrome_service = ChromeService(executable_path=ChromeDriverManager().install())
        return webdriver.Chrome(service=chrome_service, options=chrome_options)
    except Exception as e:
        logging.error(f"Failed to initialize WebDriver: {e}")
        raise

def fetch_dynamic_content(url, source_name, retries=3):
    """Fetch articles from dynamically loaded websites using Selenium."""
    for attempt in range(retries):
        try:
            driver = initialize_webdriver()
            driver.set_page_load_timeout(120)  # Increased timeout duration
            driver.get(url)
            logging.info(f"Accessed {url}, page title: {driver.title}")
            WebDriverWait(driver, 120).until(EC.presence_of_element_located((By.TAG_NAME, "a")))  # Wait until links are loaded
            articles = driver.find_elements(By.XPATH, "//article//a")  # Adjust XPath for articles
            results = []
            for article in articles:
                title = article.text.strip()
                link = article.get_attribute("href")
                if title and link and any(keyword.lower() in title.lower() for keyword in KEYWORDS):
                    results.append({"title": title, "link": link, "source": source_name})
            driver.quit()  # Close the browser to free up memory after each site scrape
            logging.info(f"Found {len(results)} articles from {source_name}")
            return results
        except Exception as e:
            logging.error(f"Attempt {attempt + 1} failed for {url}: {e}")
            time.sleep(2 ** attempt)  # Exponential backoff
    logging.error(f"Failed to scrape {url} after {retries} attempts")
    return []

def save_to_csv(articles, filename):
    """Save articles to a CSV file."""
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Source", "Title", "Link", "Keywords Used"])
        for article in articles:
            source = article.get("source", "").strip()
            title = article.get("title", "").strip().replace(",", "").replace('"', "")
            link = f'=HYPERLINK("{article.get("link", "")}", "Link")'
            keywords = ", ".join(article.get("keywords", []))
            writer.writerow([source, title, link, keywords])

def filter_articles_by_keywords(articles, keywords):
    """Filter articles based on keywords."""
    filtered_articles = []
    keyword_counts = {keyword: 0 for keyword in keywords}
    for article in articles:
        title = article.get("title", "").lower()
        matching_keywords = [keyword for keyword in keywords if keyword.lower() in title]
        if matching_keywords:
            article["keywords"] = matching_keywords
            filtered_articles.append(article)
            for keyword in matching_keywords:
                keyword_counts[keyword] += 1
    logging.info(f"Filtered {len(filtered_articles)} articles matching keywords.")
    logging.info(f"Keyword usage: {keyword_counts}")
    return filtered_articles

# --- Main Script ---
def main():
    logging.info("News Sentinel started.")
    all_articles = []

    # --- Fetch articles from dynamic websites ---
    for source_name, url in WEBSITES.items():
        logging.info(f"Scraping articles from dynamic site: {source_name}")
        articles = fetch_dynamic_content(url, source_name)
        all_articles.extend(articles)

    # --- Log total articles fetched ---
    logging.info(f"Total articles fetched: {len(all_articles)}")
    for article in all_articles:
        logging.info(f"Article: {article.get('title')}")

    # --- Filter articles by keywords ---
    filtered_articles = filter_articles_by_keywords(all_articles, KEYWORDS)

    # --- Ensure minimum 100 articles ---
    if len(filtered_articles) < 100:
        logging.warning("Fewer than 100 articles found. Adding unfiltered articles to meet the quota.")
        additional_articles = [article for article in all_articles if article not in filtered_articles]
        filtered_articles += additional_articles[:100 - len(filtered_articles)]
    logging.info(f"Total articles after fallback: {len(filtered_articles)}")

    # --- Save to CSV ---
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"news_{timestamp}.csv"
    save_to_csv(filtered_articles, output_file)
    logging.info(f"Saved {len(filtered_articles)} articles to {output_file}")

if __name__ == "__main__":
    main()
