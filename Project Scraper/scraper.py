# Import necessary libraries
import requests
from bs4 import BeautifulSoup
import csv
import datetime
import json
import re
import os
import time
import random  # Used for shuffling keywords

# Load configuration from config.json
# This function reads the configuration file and returns the keywords and websites.
def load_config():
    with open('config.json', 'r') as config_file:
        return json.load(config_file)

# Function to extract keywords from the article's text
# Matches keywords from the text using a case-insensitive search.
def extract_keywords(text, keywords):
    # Shuffle keywords to ensure diversity
    shuffled_keywords = keywords[:]
    random.shuffle(shuffled_keywords)

    # Match keywords in the article content
    matches = [keyword for keyword in shuffled_keywords if re.search(r'\b' + re.escape(keyword) + r'\b', text, re.IGNORECASE)]
    return matches

# Function to fetch articles from a website
# This function scrapes the articles from a given URL and looks for matches to the keywords.
def fetch_articles(url, keywords, error_log):
    print(f"Scraping {url}...")  # Log the website being scraped

    # Set the User-Agent header to mimic a real browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        # Fetch the webpage
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        # Log any errors encountered while fetching the website
        print(f"Error fetching {url}: {e}")
        error_log.append([str(datetime.datetime.now()), url, str(e)])
        return []  # Return an empty list if there was an error

    # Parse the page content
    soup = BeautifulSoup(response.content, 'html.parser')

    articles = []  # List to store scraped articles

    # Extract all article links and their corresponding content
    for article_tag in soup.find_all(['article', 'section']):
        # Extract the article's title
        title_tag = article_tag.find(['h1', 'h2'])  # Common tags for titles
        if title_tag:
            title = title_tag.get_text(strip=True)
        else:
            title = "No Title Found"  # Default if no title is found

        # Extract the article's link
        link_tag = article_tag.find('a', href=True)
        if not link_tag:
            continue  # Skip if no link is found
        link = link_tag['href']

        # Convert relative URLs to absolute URLs
        if not link.startswith('http'):
            link = requests.compat.urljoin(url, link)

        # Extract the article's main content for keyword matching
        body_tag = article_tag.find(['article', 'section', 'div', {'class': 'content'}])  # Adjust based on site structure
        if body_tag:
            article_content = body_tag.get_text(strip=True)
            matched_keywords = extract_keywords(article_content, keywords)  # Find matching keywords

            # Add the article to the list if any keywords are found
            if matched_keywords:
                articles.append({
                    'title': title,
                    'link': link,
                    'keywords': ', '.join(matched_keywords)
                })

    return articles  # Return the list of articles

# Function to save articles to CSV while avoiding duplicates
def save_to_csv(articles, websites, error_log):
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    csv_filename = f"scraper_{timestamp}.csv"

    # Use a set to track unique articles based on their headline and link
    unique_entries = set()

    # Track keyword usage
    keyword_usage = {}

    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Headline', 'Link', 'Keywords']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()

        # Track processed websites
        processed_websites = {article['link'].split('/')[2].replace('www.', '') for article in articles}

        # Write all unique articles to the CSV
        for article in articles:
            # Create a unique identifier for each article (based on title and link)
            unique_id = (article['title'], article['link'])
            if unique_id not in unique_entries:  # Only add if it's not already included
                unique_entries.add(unique_id)

                # Track keyword usage
                for keyword in article['keywords'].split(', '):
                    keyword_usage[keyword] = keyword_usage.get(keyword, 0) + 1

                website_name = article['link'].split('/')[2].replace('www.', '')  # Extract the website name
                writer.writerow({
                    'Headline': article['title'],
                    'Link': f'=HYPERLINK("{article["link"]}", "{website_name}")',
                    'Keywords': article['keywords']
                })

        # Add rows for websites with no matching articles
        for website in websites:
            domain = website.split('/')[2].replace('www.', '')  # Extract the domain from the URL
            if domain not in processed_websites:
                writer.writerow({
                    'Headline': domain,
                    'Link': f'=HYPERLINK("{website}", "{domain}")',
                    'Keywords': ""
                })

    # Display keyword usage stats
    print("\nKeyword Usage Statistics:")
    for keyword, count in sorted(keyword_usage.items(), key=lambda x: -x[1]):
        print(f"{keyword}: {count}")

    print(f"\nResults saved to {csv_filename}")

    # Save the error log to a separate file
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

# Main function to run the scraper
def main():
    # Load keywords and websites from the config file
    config = load_config()
    keywords = config['KEYWORDS']
    websites = config['WEBSITES']
    error_log = []  # Initialize an empty error log

    all_articles = []  # List to store all scraped articles

    # Scrape each website listed in the config
    for website in websites:
        articles = fetch_articles(website, keywords, error_log)
        all_articles.extend(articles)
        time.sleep(2)  # Delay between requests to avoid overwhelming servers

    # Save the results and error log to CSV files
    save_to_csv(all_articles, websites, error_log)

# Run the script if executed directly
if __name__ == "__main__":
    main()
