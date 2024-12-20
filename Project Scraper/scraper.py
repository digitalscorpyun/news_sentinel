import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import csv
import concurrent.futures  # For parallel execution

# Load configuration from config.json
def load_config():
    with open('config.json', 'r') as config_file:
        return json.load(config_file)

# Function to extract keywords from the article's text
def extract_keywords(text, keywords):
    matches = [keyword for keyword in keywords if keyword.lower() in text.lower()]
    return matches

# Function to fetch articles from a website
def fetch_articles(url, keywords, error_log):
    print(f"Scraping {url}...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)  # Timeout added
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')  # Faster parser
        articles = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            if not href.startswith('http'):
                href = url + href  # Handle relative links
            if href and len(href) > 5:
                title = link.get_text(strip=True) or "No Title Found"
                article_text = requests.get(href, headers=headers, timeout=10).text  # Timeout added
                matched_keywords = extract_keywords(article_text, keywords)
                if matched_keywords:
                    articles.append({
                        'headline': title,
                        'link': href,
                        'keywords': ', '.join(matched_keywords)
                    })
        return articles
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        error_log.append({'url': url, 'error': str(e)})
        return []

# Main function with parallel scraping
def main():
    config = load_config()
    keywords = config.get("KEYWORDS", [])
    websites = config.get("WEBSITES", [])
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    output_file = f"scraper_{timestamp}.csv"
    error_log_file = f"scraper_log_{timestamp}.csv"
    
    scraped_articles = []
    error_log = []

    # Use ThreadPoolExecutor for parallel execution
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(fetch_articles, website, keywords, error_log) for website in websites]
        
        for future in concurrent.futures.as_completed(futures):
            scraped_articles.extend(future.result())

    # Ensure at least one link per website
    for website in websites:
        if not any(article['link'].startswith(website) for article in scraped_articles):
            scraped_articles.append({
                'headline': website,
                'link': website,
                'keywords': 'No matching articles found'
            })

    # Check for duplicates and remove them
    unique_articles = {article['link']: article for article in scraped_articles}
    scraped_articles = list(unique_articles.values())

    # Minimum threshold check
    if len(scraped_articles) < 100:
        print(f"Warning: Only {len(scraped_articles)} articles scraped. Minimum threshold of 100 not met.")

    # Write to CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=['headline', 'link', 'keywords'])
        writer.writeheader()
        writer.writerows(scraped_articles)

    # Write error log to CSV
    if error_log:
        with open(error_log_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=['url', 'error'])
            writer.writeheader()
            writer.writerows(error_log)

    print(f"Scraping complete. Results saved to {output_file}")
    if error_log:
        print(f"Errors logged in {error_log_file}")

if __name__ == "__main__":
    main()
