import requests
import feedparser
import csv
import logging
from datetime import datetime
import os
import subprocess

# Configure logging
logging.basicConfig(
    filename="news_sentinel.log",
    level=logging.INFO,
    format="[%(asctime)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Define constants
KEYWORDS = ["AI", "artificial intelligence", "machine learning", "deep learning", "Python"]
EXCLUDED_SOURCES = ["https://blavity.com/rss"]
RSS_FEEDS = {
    "The New York Times": "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
    "The Atlantic": "https://www.theatlantic.com/feed/all/",
    "Blavity": "https://blavity.com/rss",
    "The Root": "https://www.theroot.com/rss",
    "Black Enterprise": "https://www.blackenterprise.com/feed/",
    "NPR": "https://www.npr.org/rss/rss.php?id=1001",
    "Reuters": "https://feeds.reuters.com/reuters/topNews",
    "CNET": "https://www.cnet.com/rss/news/",
    "Wired": "https://www.wired.com/feed/rss",
    "The Verge": "https://www.theverge.com/rss/index.xml",
    "TechCrunch": "https://techcrunch.com/feed/",
    "Mashable": "https://mashable.com/feeds/rss/all",
    "BBC News": "https://www.bbc.co.uk/news/rss.xml",
    "The Guardian": "https://www.theguardian.com/world/rss",
    "USA Today": "https://www.usatoday.com/rss/news/"
}

OUTPUT_FILE = f"news_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
SEEN_ARTICLES = set()  # To track seen articles
MINIMUM_ARTICLES = 100  # Ensure at least 100 articles per run

# Helper function to fetch and parse RSS feeds
def fetch_feed(url):
    try:
        feed = feedparser.parse(url)
        if feed.bozo:
            logging.warning(f"Failed to parse feed: {url}")
            return []
        return feed.entries
    except Exception as e:
        logging.error(f"Error fetching feed {url}: {e}")
        return []

# Helper function to handle requests gracefully
def safe_request(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to download content from {url}: {e}")
        return None

# Ensure at least one article from each source
def ensure_one_article_per_source(all_articles, sources):
    unique_articles = []
    sources_seen = set()

    for source_name in sources:
        source_articles = [article for article in all_articles if article.get("source_name") == source_name]
        if source_articles:
            unique_articles.append(source_articles[0])  # Select the first article from this source
            sources_seen.add(source_name)
        else:
            logging.warning(f"No articles found for source: {source_name}")

    return unique_articles

# Filter articles based on keywords
def filter_articles_by_keywords(articles, keywords):
    filtered = []
    for article in articles:
        title = article.get("title", "").lower()
        description = article.get("summary", "").lower()  # Use "summary" for description
        if any(keyword.lower() in (title + description) for keyword in keywords):
            filtered.append(article)
    return filtered

# Save articles to CSV
def save_to_csv(articles, filename):
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["title", "link", "source"])
        for article in articles:
            writer.writerow([
                article.get("title"),
                f'=HYPERLINK("{article.get("link")}")',
                article.get("source_name")
            ])

# Automate Git tracking and pushing
def git_automate():
    commit_message = f"Automated update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    try:
        repo_path = os.getcwd()  # Assume the script is run from the repository root
        subprocess.run(["git", "add", "--all"], check=True, cwd=repo_path)
        subprocess.run(["git", "commit", "-m", commit_message], check=True, cwd=repo_path)
        subprocess.run(["git", "push", "origin", "master"], check=True, cwd=repo_path)
        logging.info("Changes have been successfully pushed to the repository.")
    except subprocess.CalledProcessError as e:
        logging.error(f"An error occurred while pushing changes to GitHub: {e}")

# Main script
def main():
    logging.info("News Sentinel script started.")

    all_articles = []
    for source_name, feed_url in RSS_FEEDS.items():
        if feed_url in EXCLUDED_SOURCES:
            logging.info(f"Skipping excluded source: {feed_url}")
            continue

        logging.info(f"Fetching articles from {source_name}")
        entries = fetch_feed(feed_url)

        for entry in entries:
            article_id = entry.get("link", "")  # Use link as a unique identifier
            if article_id not in SEEN_ARTICLES:
                all_articles.append({
                    "title": entry.get("title", ""),
                    "link": entry.get("link", ""),
                    "source_name": source_name,
                    "summary": entry.get("summary", "")
                })
                SEEN_ARTICLES.add(article_id)

    logging.info(f"Total articles fetched: {len(all_articles)}")

    # Ensure at least one article per source
    unique_articles = ensure_one_article_per_source(all_articles, RSS_FEEDS.keys())
    logging.info(f"Total unique articles by source: {len(unique_articles)}")

    # Apply keyword filtering
    filtered_articles = filter_articles_by_keywords(unique_articles, KEYWORDS)
    logging.info(f"Total articles matching keywords: {len(filtered_articles)}")

    # Ensure at least MINIMUM_ARTICLES are saved
    if len(filtered_articles) < MINIMUM_ARTICLES:
        remaining_articles = [article for article in all_articles if article not in filtered_articles]
        while len(filtered_articles) < MINIMUM_ARTICLES and remaining_articles:
            filtered_articles.append(remaining_articles.pop(0))
        logging.info(f"Added additional articles to meet minimum quota of {MINIMUM_ARTICLES}.")

    # Save to CSV
    save_to_csv(filtered_articles, OUTPUT_FILE)
    logging.info(f"Saved {len(filtered_articles)} articles to {OUTPUT_FILE}")

    # Automate Git push
    git_automate()

    logging.info("News Sentinel script completed successfully.")

if __name__ == "__main__":
    main()
