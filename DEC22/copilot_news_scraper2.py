import requests
from bs4 import BeautifulSoup
import csv
import json
import logging
from datetime import datetime
from urllib.parse import urlparse

# --- Configuration ---
CONFIG = {}
try:
    with open("config.json", "r") as config_file:
        CONFIG = json.load(config_file)
except FileNotFoundError:
    logging.error("Configuration file not found.")
    exit(1)

# --- Global Variables ---
KEYWORDS = CONFIG.get("KEYWORDS", [])

# --- Logging Setup ---
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_filename = f"copilot_news_scraper_log_{timestamp}.log"
logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
logging.getLogger().addHandler(console_handler)

logging.info("Script execution started.")  # Log the script start

# Updated User-Agent to mimic a regular browser
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
}

# --- Persistent Storage for Seen Articles ---
def load_seen_articles(filename="seen_articles.json"):
    """Load previously seen articles from a JSON file."""
    try:
        with open(filename, "r") as file:
            return set(json.load(file))  # Load as a set for fast lookups
    except FileNotFoundError:
        logging.info(f"{filename} not found. Starting fresh.")
        return set()  # Return an empty set if the file doesn't exist

def save_seen_articles(seen_articles, filename="seen_articles.json"):
    """Save seen articles to a JSON file."""
    with open(filename, "w") as file:
        json.dump(list(seen_articles), file)  # Convert set to list for JSON serialization

def get_source_name(url):
    """Extract the source name from a URL."""
    domain = urlparse(url).netloc
    parts = domain.split('.')
    return parts[-2].upper() if len(parts) > 2 else parts[0].upper()

def fetch_articles(url):
    """Fetch articles from a website using BeautifulSoup."""
    logging.info(f"Fetching articles from {url}")
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = []

        # Common selectors for articles
        selectors = ["h1 a", "h2 a", "h3 a", "h4 a", "article a", "div.article a", "header a"]

        for selector in selectors:
            for link in soup.select(selector):
                title = link.text.strip()
                href = link.get('href')
                if title and href:
                    if any(keyword.lower() in title.lower() for keyword in KEYWORDS):
                        # Ensure full URLs for links
                        if href.startswith('/'):
                            href = url.rstrip('/') + href
                        articles.append({"title": title, "link": href, "source": get_source_name(url)})
                    else:
                        logging.info(f"Filtered out by keyword: {title}")
                else:
                    logging.info(f"Missing title or href: {link}")
        
        logging.info(f"Retrieved {len(articles)} articles from {url}")
        return articles
    except Exception as e:
        logging.error(f"Error fetching articles from {url}: {e}")
        return []

def save_to_csv(articles, filename, seen_articles):
    """Save unique articles to a CSV file and update seen_articles."""
    if not articles:
        logging.warning("No articles to save to CSV.")
        return

    new_articles = []
    for article in articles:
        identifier = (article["title"], article["link"])  # Use a tuple as a unique identifier
        if identifier not in seen_articles:
            new_articles.append(article)
            seen_articles.add(identifier)  # Add to the seen list

    if not new_articles:
        logging.info("No new articles found. Nothing to save.")
        return

    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Publisher_Name", "Headline_Title", "Link"])
        for article in new_articles:
            logging.info(f"Saving article: {article['source']} - {article['title']}")  # Log each saved article
            writer.writerow([
                article["source"],
                article["title"],
                f'=HYPERLINK("{article["link"]}", "Link")'
            ])
    logging.info(f"Saved {len(new_articles)} new articles to {filename}")

def main():
    logging.info("Starting article scraping...")
    all_articles = []
    max_retries = 3

    # Load previously seen articles
    seen_articles = load_seen_articles()

    dynamic_websites = [
        "https://www.technologyreview.com/",
        "https://www.cnn.com",
        # Add more websites as needed
    ]

    for url in dynamic_websites:
        articles = []
        for attempt in range(max_retries):
            articles = fetch_articles(url)
            if articles:
                break
            logging.warning(f"Retrying {url} (Attempt {attempt+1}/{max_retries})...")

        all_articles.extend(articles)
        logging.info(f"Total articles collected so far: {len(all_articles)}")

    if len(all_articles) < 100:
        logging.warning("Fewer than 100 articles found. Adjusting search criteria or adding more websites might be necessary.")

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_file = f"articles_{timestamp}.csv"
    save_to_csv(all_articles, output_file, seen_articles)

    # Save updated seen articles
    save_seen_articles(seen_articles)

    logging.info(f"Scraping completed. Articles saved to {output_file}")

if __name__ == "__main__":
    main()
