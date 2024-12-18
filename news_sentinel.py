import sys
from patched_imghdr import what
sys.modules['imghdr'] = sys.modules[__name__]

import requests
import feedparser
import csv
import logging
from datetime import datetime
import os
import subprocess
import argparse
from collections import defaultdict
from nltk.stem import PorterStemmer
from bs4 import BeautifulSoup
import tweepy

# Configure logging dynamically
parser = argparse.ArgumentParser()
parser.add_argument('--log-to-console', action='store_true', help="Log to console instead of file")
args = parser.parse_args()

if args.log_to_console:
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
else:
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

SCRAPING_SITES = {
    "Example News": "https://example.com/news"
}

# API Keys for external integrations
NEWS_API_KEY = "your_news_api_key"
NEWS_API_URL = "https://newsapi.org/v2/everything"
TWITTER_API_KEY = "your_twitter_api_key"
TWITTER_API_SECRET = "your_twitter_api_secret"
TWITTER_ACCESS_TOKEN = "your_access_token"
TWITTER_ACCESS_SECRET = "your_access_secret"

OUTPUT_FILE = f"news_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
SEEN_ARTICLES = set()  # To track seen articles
MINIMUM_ARTICLES = 100  # Ensure at least 100 articles per run

stemmer = PorterStemmer()

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

# Retry fetching feeds for robustness
def fetch_feed_with_retry(url, retries=3):
    for attempt in range(retries):
        articles = fetch_feed(url)
        if articles:
            return articles
        logging.warning(f"Retrying feed: {url} (Attempt {attempt + 1}/{retries})")
    return []

# Fetch articles from NewsAPI
def fetch_newsapi_articles(keywords):
    try:
        articles = []
        for keyword in keywords:
            params = {
                "q": keyword,
                "apiKey": NEWS_API_KEY,
                "pageSize": 20  # Fetch up to 20 articles per keyword
            }
            response = requests.get(NEWS_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            for article in data.get("articles", []):
                articles.append({
                    "title": article["title"],
                    "link": article["url"],
                    "source_name": article["source"]["name"],
                    "summary": article.get("description", "")
                })
        return articles
    except Exception as e:
        logging.error(f"Failed to fetch from NewsAPI: {e}")
        return []

# Authenticate with Twitter API
def authenticate_twitter():
    auth = tweepy.OAuthHandler(TWITTER_API_KEY, TWITTER_API_SECRET)
    auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET)
    return tweepy.API(auth)

# Fetch tweets based on keywords
def fetch_twitter_articles(keywords, api):
    try:
        articles = []
        for keyword in keywords:
            for tweet in tweepy.Cursor(api.search_tweets, q=keyword, lang="en").items(10):  # Fetch up to 10 tweets per keyword
                articles.append({
                    "title": tweet.text[:50] + "...",  # Use the first 50 characters as title
                    "link": f"https://twitter.com/i/web/status/{tweet.id}",
                    "source_name": "Twitter",
                    "summary": tweet.text
                })
        return articles
    except Exception as e:
        logging.error(f"Failed to fetch tweets: {e}")
        return []

# Scrape articles from websites
def scrape_site(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")

        articles = []
        for article in soup.find_all("div", class_="article-class"):  # Update class based on the website structure
            title = article.find("h2").text
            link = article.find("a")["href"]
            articles.append({"title": title, "link": link, "source_name": url})
        return articles
    except Exception as e:
        logging.error(f"Failed to scrape {url}: {e}")
        return []

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

# Filter articles based on keywords using stemming
def filter_articles_by_keywords(articles, keywords):
    filtered = []
    stemmed_keywords = [stemmer.stem(keyword.lower()) for keyword in keywords]

    for article in articles:
        title = article.get("title", "").lower()
        description = article.get("summary", "").lower()  # Use "summary" for description
        title_stems = [stemmer.stem(word) for word in title.split()]
        description_stems = [stemmer.stem(word) for word in description.split()]

        if any(keyword in title_stems + description_stems for keyword in stemmed_keywords):
            filtered.append(article)
    return filtered

# Save articles to CSV
def save_to_csv(articles, filename):
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["title", "link", "source", "direct_link"])
        for article in articles:
            writer.writerow([
                article.get("title"),
                f'=HYPERLINK("{article.get("link")}")',
                article.get("source_name"),
                article.get("link")
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

    # Fetch from RSS feeds
    for source_name, feed_url in RSS_FEEDS.items():
        if feed_url in EXCLUDED_SOURCES:
            logging.info(f"Skipping excluded source: {feed_url}")
            continue

        logging.info(f"Fetching articles from {source_name}")
        entries = fetch_feed_with_retry(feed_url)

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

    # Scrape websites
    for source_name, site_url in SCRAPING_SITES.items():
        logging.info(f"Scraping articles from {source_name}")
        articles = scrape_site(site_url)
        all_articles.extend(articles)

    # Fetch from NewsAPI
    logging.info("Fetching articles from NewsAPI")
    newsapi_articles = fetch_newsapi_articles(KEYWORDS)
    all_articles.extend(newsapi_articles)

    # Fetch from Twitter
    logging.info("Fetching articles from Twitter")
    twitter_api = authenticate_twitter()
    twitter_articles = fetch_twitter_articles(KEYWORDS, twitter_api)
    all_articles.extend(twitter_articles)

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
