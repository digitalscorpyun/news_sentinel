import requests
from bs4 import BeautifulSoup

# Define the URL of the news source or API
URL = 'https://example.com/news'  # Replace with the actual URL

# Function to fetch and parse articles
def fetch_articles(url):
    # Send a GET request to the URL
    response = requests.get(url)
    
    # If the request was successful
    if response.status_code == 200:
        # Parse the HTML content with BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all articles (adjust the tag/class based on the site's structure)
        articles = soup.find_all('article')  # Or use a specific tag/class for articles
        
        # Loop through each article and extract relevant information
        for article in articles:
            title = article.find('h2')  # Adjust based on the HTML structure
            summary = article.find('p')  # Adjust based on the HTML structure
            
            # Print out the title and summary of each article
            if title and summary:
                print(f"Title: {title.get_text()}")
                print(f"Summary: {summary.get_text()}")
                print('---' * 10)
    else:
        print(f'Failed to retrieve the page. Status code: {response.status_code}')

# Run the scraper
if __name__ == '__main__':
    fetch_articles(URL)
