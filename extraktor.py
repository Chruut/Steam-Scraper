from bs4 import BeautifulSoup
import csv
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import re
from datetime import datetime
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Setup Logging
logging.basicConfig(
    filename='steam_extractor.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# URL of the transaction history
TRANSACTIONS_URL = "https://store.steampowered.com/account/history/"

def get_transactions():
    try:
        # Configure Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")  # Maximize browser
        chrome_options.add_argument("--disable-notifications")  # Disable notifications
        
        # Install and start Chrome WebDriver
        logging.info("Installing Chrome WebDriver...")
        service = Service(ChromeDriverManager().install())
        
        logging.info("Starting Chrome browser...")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        try:
            # Load transactions page
            logging.info(f"Loading transactions page from: {TRANSACTIONS_URL}")
            driver.get(TRANSACTIONS_URL)
            
            # Wait for login form (if not logged in)
            try:
                username_field = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "input_username"))
                )
                logging.info("Login form found. Please log in...")
                
                # Wait for manual login
                input("Please log in and press Enter when done...")
                
                # Wait longer after login
                logging.info("Waiting for transaction page to load after login...")
                time.sleep(10)  # Wait 10 seconds after login
                
                # Wait for transaction table with longer timeout
                logging.info("Looking for transaction table...")
                WebDriverWait(driver, 60).until(  # Increase timeout to 60 seconds
                    EC.presence_of_element_located((By.CLASS_NAME, "wallet_history_row"))
                )
                logging.info("Transaction table found!")
                
                # Wait 10 seconds for manual clicks on "Load More"
                logging.info("Waiting 10 seconds for manual clicks on 'Load More'...")
                time.sleep(10)
                
            except Exception as e:
                logging.info(f"Already logged in or login not required: {str(e)}")
                # Wait a while anyway, in case the page is still loading
                time.sleep(10)
            
            # Load all available transactions
            logging.info("Loading all available transactions...")
            while True:
                try:
                    # Look for the "Load More" button
                    load_more_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "button[class*='load_more_button']"))
                    )
                    
                    # Click the button
                    logging.info("Clicking 'Load More' button...")
                    driver.execute_script("arguments[0].click();", load_more_button)
                    
                    # Wait for new transactions to load
                    time.sleep(3)
                    
                    # Check if new transactions were loaded
                    new_rows = driver.find_elements(By.CSS_SELECTOR, ".wallet_history_row")
                    if len(new_rows) <= len(rows):
                        logging.info("No new transactions loaded.")
                        break
                    
                except Exception as e:
                    logging.info("No more transactions available or button not found.")
                    break
            
            # Debug: Output page content
            logging.info("Analyzing page content...")
            logging.info(f"Page length: {len(driver.page_source)} characters")
            
            # Parse the page
            soup = BeautifulSoup(driver.page_source, "html.parser")
            
            # Debug: Find all tables on the page
            tables = soup.find_all('table')
            logging.info(f"Found tables: {len(tables)}")
            
            # Try different selectors
            rows = soup.select(".wallet_history_row") or soup.select("table.wallet_history_table tr") or soup.select("table tr")
            
            if not rows:
                logging.error("No transactions found")
                # Debug: Output HTML structure
                logging.info("Page HTML structure:")
                logging.info(soup.prettify()[:1000])  # First 1000 characters
                return []
            
            logging.info(f"Found: {len(rows)} transactions")
            
            transactions = []
            for row in rows:
                try:
                    # Debug: Output row content
                    logging.info(f"Processing row: {row}")
                    
                    # Try different selectors for the fields
                    date = (row.select_one(".wallet_history_date") or row.select_one("td:nth-child(1)")).text.strip()
                    type_cell = (row.select_one(".wallet_history_type") or row.select_one("td:nth-child(3)")).text.strip()
                    description = (row.select_one(".wallet_history_description") or row.select_one("td:nth-child(2)")).text.strip()
                    amount = (row.select_one(".wallet_history_amount") or row.select_one("td:nth-child(5)")).text.strip()
                    total = (row.select_one(".wallet_history_total") or row.select_one("td:nth-child(4)")).text.strip()
                    
                    # Only add transactions that actually contain data
                    if date and description and amount and total:
                        transactions.append({
                            'date': date,
                            'type': type_cell,
                            'description': description,
                            'amount': amount,
                            'total': total
                        })
                        logging.info(f"Transaction extracted: {date} - {type_cell} - {description} - {amount} - {total}")
                    else:
                        logging.warning(f"Incomplete transaction found: {row.text}")
                    
                except Exception as e:
                    logging.error(f"Error extracting transaction: {e}")
                    continue
            # Clean up description field by taking only first line
            for transaction in transactions:
                transaction['description'] = transaction['description'].split('\n')[0]
            return transactions
            
        finally:
            # Close browser
            logging.info("Closing browser...")
            driver.quit()
            
    except Exception as e:
        logging.error(f"Error running browser: {e}")
        return []

# Get the transactions
logging.info("Starting transaction retrieval...")
transactions = get_transactions()

# Save to CSV
logging.info(f"Found transactions: {len(transactions)}")

def parse_transaction_type(type_text):
    """Splits the type text into Type and Source at line breaks and tabs"""
    # Split at line breaks and tabs
    parts = re.split(r'[\n\t]+', type_text)
    
    # First part is the Type, the rest is the Source
    if len(parts) > 1:
        return parts[0].strip(), ' '.join(parts[1:]).strip()
    return type_text.strip(), ""

def parse_total(total_text):
    """Extracts the Total amount and checks for Credit"""
    if not total_text:
        return "", "No"
    
    # Check for Credit
    is_credit = "Credit" in total_text
    
    # Extract the amount
    amount_match = re.search(r'CHF\s*([\d.,]+)', total_text)
    if amount_match:
        return amount_match.group(1), "Yes" if is_credit else "No"
    return "", "No"

with open("steam_wallet_transactions.csv", "w", newline="", encoding='utf-8') as file:
    writer = csv.writer(file, lineterminator='\r\n')  # Windows-style line breaks
    writer.writerow(["Date", "Type", "Source", "Description", "Change", "Total", "Credit"])
    
    for trans in transactions:
        type_value, source = parse_transaction_type(trans['type'])
        total_amount, is_credit = parse_total(trans['total'])
        writer.writerow([
            trans['date'],
            type_value,
            source,
            trans['description'],
            trans['amount'],
            total_amount,
            is_credit
        ])

logging.info("CSV file has been created")
