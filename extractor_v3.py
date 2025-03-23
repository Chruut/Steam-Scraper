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

# URL der Transaktionshistorie
TRANSACTIONS_URL = "https://store.steampowered.com/account/history/"

def get_transactions():
    try:
        # Chrome-Optionen konfigurieren
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")  # Browser maximieren
        chrome_options.add_argument("--disable-notifications")  # Benachrichtigungen deaktivieren
        
        # Chrome WebDriver installieren und starten
        logging.info("Installiere Chrome WebDriver...")
        service = Service(ChromeDriverManager().install())
        
        logging.info("Starte Chrome Browser...")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        try:
            # Transaktionsseite laden
            logging.info(f"Lade Transaktionsseite von: {TRANSACTIONS_URL}")
            driver.get(TRANSACTIONS_URL)
            
            # Warte auf Login-Formular (falls nicht eingeloggt)
            try:
                username_field = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "input_username"))
                )
                logging.info("Login-Formular gefunden. Bitte loggen Sie sich ein...")
                
                # Warte auf manuelle Anmeldung
                input("Bitte loggen Sie sich ein und drücken Sie Enter, wenn Sie fertig sind...")
                
                # Warte länger nach dem Login
                logging.info("Warte auf Laden der Transaktionsseite nach Login...")
                time.sleep(10)  # Warte 10 Sekunden nach dem Login
                
                # Warte auf Transaktionstabelle mit längerem Timeout
                logging.info("Suche nach Transaktionstabelle...")
                WebDriverWait(driver, 60).until(  # Erhöhe Timeout auf 60 Sekunden
                    EC.presence_of_element_located((By.CLASS_NAME, "wallet_history_row"))
                )
                logging.info("Transaktionstabelle gefunden!")
                
                # Warte 10 Sekunden für manuelle Klicks auf "Load More"
                logging.info("Warte 10 Sekunden für manuelle Klicks auf 'Load More'...")
                time.sleep(10)
                
            except Exception as e:
                logging.info(f"Bereits eingeloggt oder Login nicht erforderlich: {str(e)}")
                # Warte trotzdem eine Weile, falls die Seite noch lädt
                time.sleep(10)
            
            # Lade alle verfügbaren Transaktionen
            logging.info("Lade alle verfügbaren Transaktionen...")
            while True:
                try:
                    # Suche nach dem "Load More" Button
                    load_more_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "button[class*='load_more_button']"))
                    )
                    
                    # Klicke den Button
                    logging.info("Klicke 'Load More' Button...")
                    driver.execute_script("arguments[0].click();", load_more_button)
                    
                    # Warte auf Laden der neuen Transaktionen
                    time.sleep(3)
                    
                    # Prüfe, ob neue Transaktionen geladen wurden
                    new_rows = driver.find_elements(By.CSS_SELECTOR, ".wallet_history_row")
                    if len(new_rows) <= len(rows):
                        logging.info("Keine neuen Transaktionen geladen.")
                        break
                    
                except Exception as e:
                    logging.info("Keine weiteren Transaktionen verfügbar oder Button nicht gefunden.")
                    break
            
            # Debug: Seiteninhalt ausgeben
            logging.info("Seiteninhalt wird analysiert...")
            logging.info(f"Seitenlänge: {len(driver.page_source)} Zeichen")
            
            # Parse die Seite
            soup = BeautifulSoup(driver.page_source, "html.parser")
            
            # Debug: Alle Tabellen auf der Seite finden
            tables = soup.find_all('table')
            logging.info(f"Gefundene Tabellen: {len(tables)}")
            
            # Versuche verschiedene Selektoren
            rows = soup.select(".wallet_history_row") or soup.select("table.wallet_history_table tr") or soup.select("table tr")
            
            if not rows:
                logging.error("Keine Transaktionen gefunden")
                # Debug: HTML-Struktur ausgeben
                logging.info("HTML-Struktur der Seite:")
                logging.info(soup.prettify()[:1000])  # Erste 1000 Zeichen
                return []
            
            logging.info(f"Gefunden: {len(rows)} Transaktionen")
            
            transactions = []
            for row in rows:
                try:
                    # Debug: Row-Inhalt ausgeben
                    logging.info(f"Verarbeite Zeile: {row}")
                    
                    # Versuche verschiedene Selektoren für die Felder
                    date = (row.select_one(".wallet_history_date") or row.select_one("td:nth-child(1)")).text.strip()
                    type_cell = (row.select_one(".wallet_history_type") or row.select_one("td:nth-child(3)")).text.strip()
                    description = (row.select_one(".wallet_history_description") or row.select_one("td:nth-child(2)")).text.strip()
                    amount = (row.select_one(".wallet_history_amount") or row.select_one("td:nth-child(5)")).text.strip()
                    total = (row.select_one(".wallet_history_total") or row.select_one("td:nth-child(4)")).text.strip()
                    
                    # Nur Transaktionen hinzufügen, die tatsächlich Daten enthalten
                    if date and description and amount and total:
                        transactions.append({
                            'date': date,
                            'type': type_cell,
                            'description': description,
                            'amount': amount,
                            'total': total
                        })
                        logging.info(f"Transaktion extrahiert: {date} - {type_cell} - {description} - {amount} - {total}")
                    else:
                        logging.warning(f"Unvollständige Transaktion gefunden: {row.text}")
                    
                except Exception as e:
                    logging.error(f"Fehler beim Extrahieren einer Transaktion: {e}")
                    continue
            # Clean up description field by taking only first line
            for transaction in transactions:
                transaction['description'] = transaction['description'].split('\n')[0]
            return transactions
            
        finally:
            # Browser schließen
            logging.info("Schließe Browser...")
            driver.quit()
            
    except Exception as e:
        logging.error(f"Fehler beim Ausführen des Browsers: {e}")
        return []

# Hole die Transaktionen
logging.info("Starte Transaktionsabruf...")
transactions = get_transactions()

# Speichere in CSV
logging.info(f"Gefundene Transaktionen: {len(transactions)}")

def parse_transaction_type(type_text):
    """Trennt den Type-Text in Type und Source an Zeilenumbrüchen und Tabulatoren"""
    # Teile an Zeilenumbrüchen und Tabulatoren
    parts = re.split(r'[\n\t]+', type_text)
    
    # Der erste Teil ist der Type, der Rest ist die Source
    if len(parts) > 1:
        return parts[0].strip(), ' '.join(parts[1:]).strip()
    return type_text.strip(), ""

def parse_total(total_text):
    """Extrahiert den Total-Betrag und prüft auf Credit"""
    if not total_text:
        return "", "Nein"
    
    # Prüfe auf Credit
    is_credit = "Credit" in total_text
    
    # Extrahiere den Betrag
    amount_match = re.search(r'CHF\s*([\d.,]+)', total_text)
    if amount_match:
        return amount_match.group(1), "Ja" if is_credit else "Nein"
    return "", "Nein"

with open("steam_wallet_transactions.csv", "w", newline="", encoding='utf-8') as file:
    writer = csv.writer(file, lineterminator='\r\n')  # Windows-Style Zeilenumbrüche
    writer.writerow(["Datum", "Type", "Source", "Beschreibung", "Change", "Total", "Credit"])
    
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

logging.info("CSV-Datei wurde erstellt")