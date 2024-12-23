import requests
from bs4 import BeautifulSoup
import csv
import json
import logging
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns

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
WEBSITES = CONFIG.get("WEBSITES", [])

# --- Logging Setup ---
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
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

logging.info("Script execution started.")  # Log the script start

def fetch_articles(url):
    """Fetch articles from a website using BeautifulSoup."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = []

        # Common selectors for articles
        selectors = ["a", "h2 a", "h3 a", "article a"]

        for selector in selectors:
            for link in soup.select(selector):
                title = link.text.strip()
                href = link.get('href')
                if title and href and any(keyword.lower() in title.lower() for keyword in KEYWORDS):
                    articles.append({"title": title, "link": href, "source": url})
        
        logging.info(f"Retrieved {len(articles)} articles from {url}")
        return articles
    except Exception as e:
        logging.error(f"Error fetching articles from {url}: {e}")
        return []

def save_to_csv(articles, filename):
    """Save articles to a CSV file with hyperlinked URLs."""
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Source", "Title", "Link"])
        for article in articles:
            writer.writerow([
                article["source"],
                article["title"],
                f'=HYPERLINK("{article["link"]}", "{article["link"]}")'
            ])

def plot_article_counts(article_counts):
    """Generate a bar chart for the number of articles fetched from each website."""
    fig, ax = plt.subplots(figsize=(10, 6))  # Adjust the figure size for better readability
    sns.barplot(x=list(article_counts.keys()), y=list(article_counts.values()), ax=ax)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right', fontsize=10)  # Rotate labels and adjust font size
    plt.xlabel('Website')
    plt.ylabel('Number of Articles')
    plt.title('Number of Articles Fetched from Each Website')
    plt.tight_layout()
    plt.show()

def main():
    logging.info("Starting article scraping...")
    all_articles = []
    article_counts = {}

    for url in WEBSITES:
        articles = fetch_articles(url)
        all_articles.extend(articles)
        article_counts[url] = len(articles)

    if len(all_articles) < 100:
        logging.warning("Fewer than 100 articles found. Adding additional unfiltered articles to reach quota.")
        all_articles += [{"title": "Placeholder Article", "link": "", "source": "Unknown"}] * (100 - len(all_articles))

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_file = f"articles_{timestamp}.csv"
    save_to_csv(all_articles, output_file)
    logging.info(f"Scraping completed. Articles saved to {output_file}")

    # Plot the number of articles fetched from each website
    plot_article_counts(article_counts)

if __name__ == "__main__":
    main()
