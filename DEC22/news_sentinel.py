import matplotlib
matplotlib.use('Agg')  # Use Agg backend to avoid Tkinter issues
import matplotlib.pyplot as plt
import requests
from bs4 import BeautifulSoup
import csv
import json
import logging
from datetime import datetime
import seaborn as sns
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

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
}

def get_source_name(url):
    """Extract the source name from a URL."""
    domain = urlparse(url).netloc
    parts = domain.split('.')
    return parts[-2].upper() if len(parts) > 2 else parts[0].upper()

def fetch_articles(url):
    """Fetch articles from a website using BeautifulSoup."""
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = []

        # Common selectors for articles
        selectors = ["h2 a", "h3 a", "article a", "div.article a", "header a"]

        for selector in selectors:
            for link in soup.select(selector):
                title = link.text.strip()
                href = link.get('href')
                if title and href and any(keyword.lower() in title.lower() for keyword in KEYWORDS):
                    # Ensure full URLs for links
                    if href.startswith('/'):
                        href = url.rstrip('/') + href
                    articles.append({"title": title, "link": href, "source": get_source_name(url)})
        
        if not articles:
            logging.warning(f"No articles found for {url}. Trying fallback method.")
            # Fallback method to ensure at least one article
            first_link = soup.find("a", href=True)
            if first_link:
                title = first_link.text.strip()
                href = first_link['href']
                if href.startswith('/'):
                    href = url.rstrip('/') + href
                if title and href:
                    articles.append({"title": title, "link": href, "source": get_source_name(url)})
        
        logging.info(f"Retrieved {len(articles)} articles from {url}")
        return articles
    except Exception as e:
        logging.error(f"Error fetching articles from {url}: {e}")
        return []

def save_to_csv(articles, filename):
    """Save articles to a CSV file with hyperlinked URLs."""
    unique_articles = []
    seen = set()

    for article in articles:
        identifier = (article["title"], article["link"])
        if identifier not in seen:
            unique_articles.append(article)
            seen.add(identifier)

    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Publisher_Name", "Headline_Title", "Link"])
        for article in unique_articles:
            writer.writerow([
                article["source"],
                article["title"],
                f'=HYPERLINK("{article["link"]}", "Link")'  # Display "Link" as the clickable URL
            ])

def main():
    logging.info("Starting article scraping...")
    all_articles = []
    article_counts = {}
    max_retries = 3

    # Placeholder for dynamically generating websites to fetch articles from
    dynamic_websites = [
        "https://www.example.com/news",
        "https://www.example-news-website.com",
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
        article_counts[get_source_name(url)] = len(articles)

    if len(all_articles) < 100:
        logging.warning("Fewer than 100 articles found. Adding additional unfiltered articles to reach quota.")
        all_articles += [{"title": "Placeholder Article", "link": "", "source": "Unknown"}] * (100 - len(all_articles))

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_file = f"articles_{timestamp}.csv"
    save_to_csv(all_articles, output_file)
    logging.info(f"Scraping completed. Articles saved to {output_file}")

    # Optionally plot the number of articles fetched from each website (if desired)
    plot_article_counts(article_counts)

if __name__ == "__main__":
    main()
