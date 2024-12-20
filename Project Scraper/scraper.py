import requests
from bs4 import BeautifulSoup
import csv
import datetime
import json
import re
import os
import time

# Load configuration from config.json
def load_config():
    with open('config.json', 'r') as config_file:
        return json.load(config_file)

# Function to extract keywords from the article's text
def extract_keywords(text, keywords):
    matches = [keyword for keyword in keywords if re.search(r'\b' + re.escape(keyword) + r'\b', text, re.IGNORECASE)]
    return matches

# Function to fetch articles from a website
def fetch_articles(url, keywords, error_log):
    print(f"Scraping {url}...")
    
    # Set the User-Agent header to mimic a real browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an error for bad status codes
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        error_log.append([str(datetime.datetime.now()), url, str(e)])  # Log the error
        return []

    # Parse the page content
    soup = BeautifulSoup(response.content, 'html.parser')

    articles = []
    
    # Extract all article links and their corresponding content
    for article_tag in soup.find_all(['article', 'section']):
        title_tag = article_tag.find(['h1', 'h2'])
        if title_tag:
            title = title_tag.get_text(strip=True)
        else:
            title = "No Title Found"

        link_tag = article_tag.find('a', href=True)
        if not link_tag:
            continue
        link = link_tag['href']
        
        # Absolute URL if it's a relative link
        if not link.startswith('http'):
            link = requests.compat.urljoin(url, link)

        body_tag = article_tag.find(['article', 'section', 'div', {'class': 'content'}])  # Adjust based on actual content class
        if body_tag:
            article_content = body_tag.get_text(strip=True)
            matched_keywords = extract_keywords(article_content, keywords)

            if matched_keywords:
                articles.append({
                    'title': title,
                    'link': link,
                    'keywords': ', '.join(matched_keywords)
                })
    
    return articles

# Function to save the articles to a CSV file
def save_to_csv(articles, websites, error_log):
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    csv_filename = f"scraper_{timestamp}.csv"

    # Open the CSV file for writing
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Headline', 'Link', 'Keywords']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()

        # Track which websites are already in the CSV
        processed_websites = {article['link'].split('/')[2].replace('www.', '') for article in articles}

        # Write all articles to the CSV
        for article in articles:
            website_name = article['link'].split('/')[2].replace('www.', '')
            writer.writerow({
                'Headline': article['title'],
                'Link': f'=HYPERLINK("{article["link"]}", "{website_name}")',
                'Keywords': article['keywords']
            })

        # Add fallback rows for websites with no matching articles
        for website in websites:
            domain = website.split('/')[2].replace('www.', '')
            if domain not in processed_websites:
                writer.writerow({
                    'Headline': "No matching articles found",
                    'Link': f'=HYPERLINK("{website}", "{domain}")',
                    'Keywords': ""
                })

    print(f"Results saved to {csv_filename}")

    # Save the error log to a CSV file
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

def main():
    config = load_config()
    keywords = config['KEYWORDS']
    websites = config['WEBSITES']
    error_log = []

    all_articles = []

    # Scrape each website
    for website in websites:
        articles = fetch_articles(website, keywords, error_log)
        all_articles.extend(articles)
        time.sleep(2)  # Delay to avoid overloading servers

    # Save articles to CSV and log errors
    save_to_csv(all_articles, websites, error_log)

if __name__ == "__main__":
    main()
