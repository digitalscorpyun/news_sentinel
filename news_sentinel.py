import requests
import feedparser
import csv
import logging
import os
import time
from datetime import datetime
from requests.exceptions import RequestException
import json
import subprocess

# --- Check and Install Missing Libraries ---
def ensure_dependencies():
    required_libraries = ["feedparser", "requests"]
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
logging.basicConfig(
    filename="news_sentinel.log",
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Add console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
logging.getLogger().addHandler(console_handler)

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

def fetch_newsapi_articles():
    """Fetch articles using NewsAPI."""
    try:
        url = f"https://newsapi.org/v2/top-headlines?language=en&pageSize=50&apiKey={CONFIG['NEWS_API_KEY']}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json().get("articles", [])
    except RequestException as e:
        logging.error(f"NewsAPI Error: {e}")
        return []

def save_to_csv(articles, filename):
    """Save articles to a CSV file."""
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Headline", "Source", "URL"])
        for article in articles:
            headline = article.get("title", "").strip()
            
            # Handle the source field
            source = article.get("source", "")
            if isinstance(source, dict):  # Extract 'name' if source is a dictionary
                source = source.get("name", "")
            source = str(source).strip()  # Convert to string and strip

            # Create clickable hyperlink
            url = f'=HYPERLINK("{article.get("link", "")}", "{article.get("link", "")}")'
            writer.writerow([headline, source, url])

# --- Main Script ---

def main():
    logging.info("News Sentinel started.")
    all_articles = []

    # Fetch articles from RSS feeds
    for source_name, url in CONFIG["RSS_FEEDS"].items():
        logging.info(f"Fetching articles from {source_name}")
        articles = fetch_rss_feed(url)
        if articles:
            for entry in articles:
                all_articles.append({
                    "title": entry.get("title", ""),
                    "link": entry.get("link", ""),
                    "source": source_name
                })
        else:
            logging.warning(f"No articles fetched from {source_name}")

    # Fetch additional articles from APIs
    all_articles += fetch_newsapi_articles()

    # Save to CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"news_{timestamp}.csv"
    save_to_csv(all_articles, output_file)
    logging.info(f"Saved {len(all_articles)} articles to {output_file}")

if __name__ == "__main__":
    main()
