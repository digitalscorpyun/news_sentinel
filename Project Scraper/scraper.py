import requests
from bs4 import BeautifulSoup
import csv
import datetime
import json
import re

# Function to load configuration from config.json
def load_config():
    with open('config.json', 'r') as config_file:
        return json.load(config_file)

# Function to extract keywords from text
def extract_keywords(text, keywords):
    matches = [keyword for keyword in keywords if re.search(r'\b' + re.escape(keyword) + r'\b', text, re.IGNORECASE)]
    return matches

# Function to scrape articles from websites
def scrape_website(url, keywords):
    try:
        # Send GET request to the URL
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        # Parse the HTML content with BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all articles (adjust based on the site's structure)
        articles = soup.find_all('article')  # Modify this as per the website structure
        extracted_data = []

        for article in articles:
            # Extract the title (adjust based on the site's structure)
            title_tag = article.find('h2')
            link_tag = article.find('a', href=True)
            
            if title_tag and link_tag:
                title = title_tag.get_text().strip()
                link = link_tag['href']
                
                # Extract keywords from the title and content
                matched_keywords = extract_keywords(title, keywords)
                
                # If keywords match, append the data
                if matched_keywords:
                    extracted_data.append({
                        'title': title,
                        'link': link,
                        'keywords': ', '.join(matched_keywords)
                    })

        return extracted_data

    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return []

# Function to save scraped data to CSV
def save_to_csv(data):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"scraper_{timestamp}.csv"
    
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csv_file:
        fieldnames = ['Headline', 'Link', 'Keywords']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in data:
            writer.writerow(row)
    
    print(f"Data saved to {csv_filename}")

# Main function to run the scraper
def main():
    # Load configuration (keywords and websites)
    config = load_config()
    keywords = config['KEYWORDS']
    websites = config['WEBSITES']
    
    # List to hold all article data
    all_articles = []
    
    # Loop through each website and scrape articles
    for website in websites:
        print(f"Scraping {website}...")
        website_data = scrape_website(website, keywords)
        all_articles.extend(website_data)
    
    # Save the collected data to CSV
    if all_articles:
        save_to_csv(all_articles)
    else:
        print("No articles found matching the keywords.")

if __name__ == '__main__':
    main()
