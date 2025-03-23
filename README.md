# Steam Transaction Analyzer

A Python tool that analyzes Steam wallet transactions and generates detailed reports in both text and Excel formats. This project helps users track their Steam spending, market transactions, and overall wallet balance.

## Features

- Parses Steam wallet transaction CSV files
- Analyzes market transactions (earnings and expenses)
- Tracks non-market expenses
- Generates detailed text analysis report
- Creates formatted Excel spreadsheet for expenses
- Calculates total earnings, expenses, and net balance
- Identifies top 5 largest transactions

## Requirements

- Python 3.x
- All required packages are listed in `requirements.txt`

## Installation

1. Clone this repository
2. Install all required packages using the provided requirements.txt:
```bash
pip install -r requirements.txt
```

This will install all necessary dependencies including:
- openpyxl (for Excel file generation)
- pandas (for data manipulation)
- numpy (for numerical operations)
- beautifulsoup4 (for HTML parsing)
- selenium (for web automation)
- webdriver-manager (for Chrome WebDriver management)

## Usage

1. Export your Steam wallet transactions as CSV from Steam
2. Place the CSV file in the project directory as `steam_wallet_transactions.csv`
3. Run the analyzer:
```bash
python analyze_transactions.py
```

## Output Files

The script generates two output files:

1. `steam_analysis.txt`: Contains a detailed summary of all transactions including:
   - Market transactions (earnings and expenses)
   - Other transactions
   - Overall summary with net balance
   - Top 5 largest transactions

2. `steam_expenses.xlsx`: A formatted Excel spreadsheet containing:
   - All non-market expenses
   - Transaction dates and descriptions
   - Amounts in CHF
   - Total sum of expenses
   - Auto-adjusted column widths for better readability

## Data Privacy Note

This project uses real Steam transaction data for development and testing purposes. The data has been generously shared by the project maintainer to help improve the tool's functionality and accuracy. All transaction data is processed locally and no information is transmitted to external servers.

## License

This project is open source and available under the MIT License.

. 
