import requests
import feedparser
import csv
import logging
import tweepy
from datetime import datetime
import os
import time

# --- Configure Logging ---
logging.basicConfig(
    filename="news_sentinel.log",
    level=logging.INFO,
    format="[%(asctime)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# --- Constants ---
KEYWORDS = ["AI", "artificial intelligence", "machine learning", "deep learning", "Python"]
NEWS_API_KEY = "your_news_api_key_here"
TWITTER_API_KEY = "your_twitter_api_key_here"
TWITTER_API_SECRET = "your_twitter_api_secret_here"
TWITTER_ACCESS_TOKEN = "your_twitter_access_token_here"
TWITTER_ACCESS_SECRET = "your_twitter_access_secret_here"

RSS_FEEDS = {
    "The New York Times": "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
    "BBC News": "https://www.bbc.co.uk/news/rss.xml",
    "TechCrunch": "https://techcrunch.com/feed/",
    "CNET": "https://www.cnet.com/rss/news/",
    "Reuters": "https://feeds.reuters.com/reuters/topNews",
    "The Guardian": "https://www.theguardian.com/world/rss",
    "Blavity": "https://blavity.com/rss",
    "Mashable": "https://mashable.com/feeds/rss/all",
    "The Atlantic": "https://www.theatlantic.com/feed/all/",
    "Black Enterprise": "https://www.blackenterprise.com/feed/",
    "USA Today": "https://www.usatoday.com/rss/news/"
}

OUTPUT_FILE = f"news_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
MINIMUM_ARTICLES = 100
SEEN_ARTICLES = set()

# --- Helper Functions ---

def fetch_rss_feed(url, retries=3):
    """Fetch articles from an RSS feed with retries."""
    for attempt in range(retries):
        try:
            feed = feedparser.parse(url)
            if not feed.bozo:
                return feed.entries
        except Exception as e:
            logging.error(f"RSS Fetch Error ({url}): {e}")
        time.sleep(2)  # Wait before retrying
    return []

def fetch_newsapi_articles():
    """Fetch articles using NewsAPI."""
    try:
        url = f"https://newsapi.org/v2/top-headlines?language=en&pageSize=50&apiKey={NEWS_API_KEY}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json().get("articles", [])
    except Exception as e:
        logging.error(f"NewsAPI Error: {e}")
        return []

def fetch_twitter_articles():
    """Fetch tweets using the Twitter API."""
    try:
        auth = tweepy.OAuthHandler(TWITTER_API_KEY, TWITTER_API_SECRET)
        auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET)
        api = tweepy.API(auth)
        tweets = api.search_tweets(q=" OR ".join(KEYWORDS), count=50, lang="en", result_type="recent")
        return [{"title": tweet.text, "link": f"https://twitter.com/i/web/status/{tweet.id}", "source": "Twitter"}
                for tweet in tweets]
    except Exception as e:
        logging.error(f"Twitter API Error: {e}")
        return []

def filter_articles_by_keywords(articles, keywords):
    """Filter articles based on keywords."""
    filtered = []
    for article in articles:
        title = article.get("title", "").lower()
        description = article.get("summary", "").lower()
        if any(keyword.lower() in (title + description) for keyword in keywords):
            filtered.append(article)
    return filtered

def save_to_csv(articles, filename):
    """Save articles to a CSV file."""
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Title", "Link", "Source"])
        for article in articles:
            writer.writerow([article.get("title"), article.get("link"), article.get("source")])

# --- Main Script ---

def main():
    logging.info("News Sentinel script started.")

    all_articles = []
    for source_name, url in RSS_FEEDS.items():
        logging.info(f"Fetching articles from {source_name}")
        articles = fetch_rss_feed(url)
        if not articles:
            logging.warning(f"No articles from {source_name}.")
        else:
            for entry in articles:
                if entry.get("link") not in SEEN_ARTICLES:
                    SEEN_ARTICLES.add(entry.get("link"))
                    all_articles.append({
                        "title": entry.get("title", ""),
                        "link": entry.get("link", ""),
                        "source": source_name,
                        "summary": entry.get("summary", "")
                    })

    # Fetch additional articles from APIs
    all_articles += fetch_newsapi_articles()
    all_articles += fetch_twitter_articles()

    # Filter and ensure minimum articles
    filtered_articles = filter_articles_by_keywords(all_articles, KEYWORDS)
    if len(filtered_articles) < MINIMUM_ARTICLES:
        logging.warning("Filling quota with non-matching articles.")
        additional_articles = [article for article in all_articles if article not in filtered_articles]
        filtered_articles += additional_articles[:MINIMUM_ARTICLES - len(filtered_articles)]

    # Save to CSV
    save_to_csv(filtered_articles, OUTPUT_FILE)
    logging.info(f"Saved {len(filtered_articles)} articles to {OUTPUT_FILE}")
    logging.info("News Sentinel script completed successfully.")

if __name__ == "__main__":
    main()
