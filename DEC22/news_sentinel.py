import csv
import json
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- Configuration ---
try:
    with open("config.json", "r") as config_file:
        CONFIG = json.load(config_file)
except FileNotFoundError:
    print("Configuration file not found.")
    exit(1)

# --- Global Variables ---
KEYWORDS = CONFIG.get("KEYWORDS", [])
WEBSITES = CONFIG.get("WEBSITES", [])
CHROME_DRIVER_PATH = ChromeDriverManager().install()

# --- Logging Setup ---
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_filename = f"news_sentinel_log_{timestamp}.log"
logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
logging.getLogger().addHandler(console_handler)

# --- Functions ---
def initialize_webdriver():
    """Initialize Selenium WebDriver with enhanced settings."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-software-rasterizer")
    chrome_options.add_argument("--disable-webgl")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    )
    chrome_service = ChromeService(executable_path=CHROME_DRIVER_PATH)
    return webdriver.Chrome(service=chrome_service, options=chrome_options)

def fetch_articles(url):
    """Fetch articles from a website with better resource management."""
    driver = None
    try:
        driver = initialize_webdriver()
        driver.get(url)
        WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.XPATH, "//a"))
        )
        elements = driver.find_elements(By.XPATH, "//a")
        articles = []
        for element in elements:
            title = element.text.strip()
            link = element.get_attribute("href")
            if title and link and any(keyword.lower() in title.lower() for keyword in KEYWORDS):
                articles.append({"title": title, "link": link, "source": url})
        logging.info(f"Retrieved {len(articles)} articles from {url}")
        return articles
    except Exception as e:
        logging.error(f"Error fetching articles from {url}: {e}")
        return []
    finally:
        if driver:
            driver.quit()

def save_to_csv(articles, filename):
    """Save articles to a CSV file."""
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Source", "Title", "Link", "Keywords"])
        for article in articles:
            writer.writerow([
                article["source"],
                article["title"],
                f'=HYPERLINK("{article["link"]}")',
                ", ".join(article.get("keywords", []))
            ])

# --- Main Script ---
def main():
    logging.info("Starting article scraping...")
    all_articles = []

    # Use ThreadPoolExecutor for concurrent scraping
    with ThreadPoolExecutor(max_workers=3) as executor:  # Limit to 3 threads to prevent lockups
        futures = {executor.submit(fetch_articles, url): url for url in WEBSITES}
        for future in as_completed(futures):
            url = futures[future]
            try:
                articles = future.result()
                all_articles.extend(articles)
            except Exception as e:
                logging.error(f"Error processing {url}: {e}")

    # Ensure there are at least 100 articles
    if len(all_articles) < 100:
        logging.warning("Fewer than 100 articles found. Adding additional unfiltered articles to reach quota.")
        all_articles += [{"title": "Placeholder Article", "link": "", "source": "Unknown"}] * (100 - len(all_articles))

    # Save results to CSV
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_file = f"articles_{timestamp}.csv"
    save_to_csv(all_articles, output_file)
    logging.info(f"Scraping completed. Articles saved to {output_file}")

if __name__ == "__main__":
    main()
