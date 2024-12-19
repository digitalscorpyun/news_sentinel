import requests
from bs4 import BeautifulSoup
import csv
import datetime
import json
import re
import os

# Load configuration from config.json
def load_config():
    with open('config.json', 'r') as config_file:
        return json.load(config_file)

# Function to extract keywords from the article's text
def extract_keywords(text, keywords):
    # Case insensitive match for keywords
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
        # Fetch the webpage
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
        # Extract title (headline)
        title_tag = article_tag.find(['h1', 'h2'])
        if title_tag:
            title = title_tag.get_text(strip=True)
        else:
            title = "No Title Found"

        # Extract the article's link
        link_tag = article_tag.find('a', href=True)
        if not link_tag:
            continue
        link = link_tag['href']
        
        # Absolute URL if it's a relative link
        if not link.startswith('http'):
            link = requests.compat.urljoin(url, link)

        # Extract content from the article's main body
        body_tag = article_tag.find(['article', 'section', 'div', {'class': 'content'}])  # Adjust based on actual content class
        if body_tag:
            article_content = body_tag.get_text(strip=True)
            matched_keywords = extract_keywords(article_content, keywords)

            # Only include articles that match at least one keyword
            if matched_keywords:
                articles.append({
                    'title': title,
                    'link': link,
                    'keywords': ', '.join(matched_keywords)
                })
    
    return articles

# Function to save the CSV file for the articles
def save_to_csv(articles, error_log):
    # Define the current date and time for the filenames
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

    # Save the articles to a CSV file
    if articles:
        with open(f"scraper_{timestamp}.csv", 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Headline', 'Link', 'Keywords']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for article in articles:
                # Convert the link to just the website name and hyperlink the URL
                website_name = article['link'].split('/')[2].replace('www.', '')
                writer.writerow({
                    'Headline': article['title'],
                    'Link': f'=HYPERLINK("{article["link"]}", "{website_name}")',
                    'Keywords': article['keywords']
                })

    # Save the error log CSV
    if error_log:
        with open(f"scraper_log_{timestamp}.csv", 'w', newline='', encoding='utf-8') as logfile:
            fieldnames = ['Timestamp', 'URL', 'Error']
            writer = csv.DictWriter(logfile, fieldnames=fieldnames)
            writer.writeheader()
            for error in error_log:
                writer.writerow({
                    'Timestamp': error[0],
                    'URL': error[1],
                    'Error': error[2]
                })
    else:
        print("No errors to log.")

# Main scraping function
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
        time.sleep(2)  # Add a delay between requests to avoid hitting the server too hard

    # Save articles to CSV and log errors
    save_to_csv(all_articles, error_log)

if __name__ == "__main__":
    main()
