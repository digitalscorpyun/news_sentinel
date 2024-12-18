import os
import pandas as pd
import feedparser
from newspaper import Article
from datetime import datetime

# -----------------------------
# Configuration
# -----------------------------
OUTPUT_FILE = "news.csv"
LOG_FILE = "news_sentinel.log"

RSS_FEEDS = [
    "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
    "https://www.theatlantic.com/feed/all/",
    "https://blavity.com/rss",
    "https://www.theroot.com/rss",
    "https://www.blackenterprise.com/feed/",
    "https://www.npr.org/rss/rss.php?id=1001",
    "https://feeds.reuters.com/reuters/topNews",
    "https://www.cnet.com/rss/news/",
    "https://www.wired.com/feed/rss",
    "https://www.theverge.com/rss/index.xml",
    "https://techcrunch.com/feed/",
    "https://mashable.com/feeds/rss/all",
    "https://www.bbc.co.uk/news/rss.xml",
    "https://www.theguardian.com/world/rss",
    "https://www.usatoday.com/rss/news/",
    # Add all 30 RSS feeds here...
]

KEYWORDS = [
    "Black culture", "artificial intelligence", "climate change", "elections", "HBCUs",
    "Afrofuturism", "police reform", "global economy", "Black Lives Matter", "education reform",
    "healthcare access", "generational wealth", "blockchain", "sports culture", "machine learning",
    "racial justice", "cybersecurity", "poverty", "inequality"
    # Add the full 97 keywords here
]

# -----------------------------
# Utility Functions
# -----------------------------

def log_message(message):
    """Log a message to the log file with a timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as log_file:
        log_file.write(f"[{timestamp}] {message}\n")
    print(f"[{timestamp}] {message}")

def fetch_articles_from_feed(feed_url):
    """Fetch articles from an RSS feed."""
    articles = []
    try:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            articles.append({
                "title": entry.get("title", "No Title"),
                "link": entry.get("link", "No Link"),
                "source": feed.feed.get("title", "Unknown Source"),
                "summary": entry.get("summary", "")
            })
        log_message(f"Fetched {len(articles)} articles from {feed_url}")
    except Exception as e:
        log_message(f"Error fetching from {feed_url}: {e}")
    return articles

def download_full_content(article):
    """Download and extract full content from an article link."""
    url = article["link"]
    try:
        news_article = Article(url)
        news_article.download()
        news_article.parse()
        return news_article.text
    except Exception as e:
        log_message(f"Failed to download content for {url}: {e}")
        return ""

def filter_articles_by_keywords(articles, keywords):
    """Filter articles containing any of the keywords in title, summary, or full content."""
    filtered = []
    for article in articles:
        title = article.get("title", "").lower()
        summary = article.get("summary", "").lower()
        content = article.get("content", "").lower()  # Full content
        
        if any(keyword.lower() in title or keyword.lower() in summary or keyword.lower() in content for keyword in keywords):
            filtered.append(article)
    return filtered

def save_articles_to_csv(articles, filename):
    """Save articles to CSV with only title, link, and source."""
    if not articles:
        log_message("No articles to save.")
        return

    df = pd.DataFrame(articles)[["title", "link", "source"]]
    df["link"] = df["link"].apply(lambda x: f'=HYPERLINK("{x}", "Link")')
    df.to_csv(filename, index=False)
    log_message(f"Saved {len(df)} articles to {filename}")

# -----------------------------
# Main Execution
# -----------------------------

def main():
    log_message("News Sentinel script started.")
    all_articles = []

    # Step 1: Fetch articles from all feeds
    for feed_url in RSS_FEEDS:
        articles = fetch_articles_from_feed(feed_url)
        
        # Download full content for each article
        for article in articles:
            article["content"] = download_full_content(article)
        
        all_articles.extend(articles)

    log_message(f"Total articles fetched: {len(all_articles)}")

    # Step 2: Filter articles based on keywords
    filtered_articles = filter_articles_by_keywords(all_articles, KEYWORDS)
    log_message(f"Total articles matching keywords: {len(filtered_articles)}")

    # Step 3: Save to CSV
    save_articles_to_csv(filtered_articles, OUTPUT_FILE)

    log_message("News Sentinel script completed successfully.")

if __name__ == "__main__":
    main()
