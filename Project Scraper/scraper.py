# Import necessary libraries
import requests
from bs4 import BeautifulSoup
import csv
import datetime
import json
import re
import os
import time
import random

# Load configuration from config.json
def load_config():
    with open('config.json', 'r') as config_file:
        return json.load(config_file)

# Function to extract keywords with frequency balancing
def extract_keywords(text, keywords, keyword_counts):
    # Shuffle keywords to introduce randomness
    shuffled_keywords = keywords[:]
    random.shuffle(shuffled_keywords)

    # Match keywords and prioritize less frequent ones
    matches = []
    for keyword in shuffled_keywords:
        if re.search(r'\b' + re.escape(keyword) + r'\b', text, re.IGNORECASE):
            matches.append(keyword)
            # Increment the keyword usage count
            keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
            # Limit the number of "Black" keyword matches
            if keyword.lower() == "black" and keyword_counts[keyword] > 5:
                continue

    return matches

# Function to fetch articles and improve headline extraction
def fetch_articles(url, keywords, keyword_counts, error_log):
    print(f"Scraping {url}...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        error_log.append([str(datetime.datetime.now()), url, str(e)])
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    articles = []

    # Look for articles and try multiple strategies for headline extraction
    for article_tag in soup.find_all(['article', 'section']):
        title = None

        # Attempt to find the title in common headline tags
        for tag in ['h1', 'h2', 'h3', 'title']:
            title_tag = article_tag.find(tag)
            if title_tag:
                title = title_tag.get_text(strip=True)
                break

        # Fallback to extract meaningful content if no title is found
        if not title:
            first_paragraph = article_tag.find('p')
            title = first_paragraph.get_text(strip=True) if first_paragraph else "No Title Found"

        link_tag = article_tag.find('a', href=True)
        if not link_tag:
            continue
        link = link_tag['href']
        if not link.startswith('http'):
            link = requests.compat.urljoin(url, link)

        body_tag = article_tag.find(['article', 'section', 'div', {'class': 'content'}])
        if body_tag:
            article_content = body_tag.get_text(strip=True)
            matched_keywords = extract_keywords(article_content, keywords, keyword_counts)
            if matched_keywords:
                articles.append({
                    'title': title,
                    'link': link,
                    'keywords': ', '.join(matched_keywords)
                })

    return articles

# Function to save articles to CSV while balancing keyword diversity and avoiding duplicates
def save_to_csv(articles, websites, error_log, keyword_counts):
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    csv_filename = f"scraper_{timestamp}.csv"
    unique_entries = set()

    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Headline', 'Link', 'Keywords']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        processed_websites = {article['link'].split('/')[2].replace('www.', '') for article in articles}

        for article in articles:
            unique_id = (article['title'], article['link'])
            if unique_id not in unique_entries:
                unique_entries.add(unique_id)
                website_name = article['link'].split('/')[2].replace('www.', '')
                writer.writerow({
                    'Headline': article['title'],
                    'Link': f'=HYPERLINK("{article["link"]}", "{website_name}")',
                    'Keywords': article['keywords']
                })

        for website in websites:
            domain = website.split('/')[2].replace('www.', '')
            if domain not in processed_websites:
                writer.writerow({
                    'Headline': domain,
                    'Link': f'=HYPERLINK("{website}", "{domain}")',
                    'Keywords': ""
                })

    print("\nKeyword Usage Statistics:")
    for keyword, count in sorted(keyword_counts.items(), key=lambda x: -x[1]):
        print(f"{keyword}: {count}")

    print(f"\nResults saved to {csv_filename}")

    if error_log:
        error_log_filename = f"scraper_log_{timestamp}.csv"
        with open(error_log_filename, 'w', newline='', encoding='utf-8') as logfile:
            fieldnames = ['Timestamp', 'URL', 'Error']
            writer = csv.writer(logfile)
            writer.writerow(fieldnames)
            writer.writerows(error_log)
        print(f"Error log saved to {error_log_filename}")
    else:
        print("No errors to log.")

# Main function
def main():
    config = load_config()
    keywords = config['KEYWORDS']
    websites = config['WEBSITES']
    error_log = []
    keyword_counts = {}  # Track keyword usage for balancing

    all_articles = []
    for website in websites:
        articles = fetch_articles(website, keywords, keyword_counts, error_log)
        all_articles.extend(articles)
        time.sleep(2)

    save_to_csv(all_articles, websites, error_log, keyword_counts)

if __name__ == "__main__":
    main()
