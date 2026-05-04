# Personal Finance Tracker

A modular personal finance tracking application built with Python and Streamlit, designed for engineering students and professionals to demonstrate technical skills while managing personal finances.

## Project Structure

```
finance_tracker/
│
├── main.py                 # Main Streamlit application
├── database.py             # Database operations and models
├── csv_parser.py           # CSV parsing and data cleaning
├── sample_data.py          # Sample data generation
├── requirements.txt        # Python dependencies
├── README.md              # This file
└── finance.db             # SQLite database (auto-created)
```

## Quick Start

### Installation
1. Install dependencies:
```bash
pip install streamlit pandas plotly
```

2. Run the application:
```bash
streamlit run main.py
```

3. Navigate to the displayed URL (usually http://localhost:8501)

## Features

- **SCADA-Style Dashboard**: Real-time financial metrics with industrial control system aesthetics
- **Intelligent CSV Parsing**: Handles multiple bank formats with automatic currency cleaning
- **Duplicate Detection**: Prevents re-importing the same transactions from overlapping CSV files
- **Investment Account Management**: Simple balance tracking for brokerage, IRA, and crypto accounts
- **Automatic Categorization**: AI-powered transaction categorization based on merchant names
- **Account Balance Sync**: Automatically updates account balances from CSV Balance columns
- **Interactive Analytics**: Spending trends, cash flow analysis, and net worth tracking

## Usage

### Bank Account Data (Checking, Savings, Credit Cards)

1. Go to "Upload Data" in the sidebar
2. Select your account type
3. Upload a CSV file from your bank
4. System automatically:
   - Detects date, description, and amount columns
   - Cleans currency formatting ($, commas, parentheses)
   - Combines separate Debit/Credit columns if needed
   - Updates account balance from Balance column
   - Skips duplicate transactions on re-upload

### Investment Accounts (Fidelity Brokerage, Roth IRA, Crypto)

For investment accounts, use the manual balance update feature instead of uploading transaction CSVs:

1. Select investment account type
2. Enter current portfolio value
3. Click "Update Balance"
4. Track contributions/withdrawals as transactions in your checking account

### Data Management

**Clear All Data:**
1. Stop the app (Ctrl+C in terminal)
2. Delete the `finance.db` file in your project directory
3. Restart with `streamlit run main.py`

**Duplicate Prevention:**
- The system automatically detects and skips duplicate transactions
- Safe to re-upload CSVs with overlapping date ranges
- Matching based on date, description, amount, and account

## Supported CSV Formats

### Standard Bank Format (Checking/Savings)
- Columns: Date, Description, Amount, Balance
- Handles currency symbols, commas, negative parentheses
- Automatically updates account balance

### Money Market Format
- Columns: Transaction Date, Transaction Type, Debit, Credit, Balance
- Combines Debit/Credit into single amount (Credit positive, Debit negative)
- Uses Transaction Type as description if no Description column

### Common Column Mappings
- **Date**: "date", "transaction date", "posted date", "trans date"
- **Description**: "description", "merchant", "payee", "memo", "transaction type"
- **Amount**: "amount", "transaction amount", "debit", "credit", "value"

## Technical Architecture

### Database Schema

**Transactions Table:**
- id, date, description, amount, category, account, transaction_type, source_file, created_at

**Accounts Table:**
- id, account_name, account_type, current_balance, target_balance, last_updated

### Module Responsibilities

- **main.py**: Streamlit UI, dashboard, and user interactions
- **database.py**: SQLite operations, duplicate detection, account management
- **csv_parser.py**: Robust CSV parsing, currency cleaning, column detection
- **sample_data.py**: Realistic sample data generation for development

## Skills Demonstrated

- **Data Engineering**: ETL pipeline with robust error handling
- **Database Design**: Normalized schema with duplicate prevention
- **Web Development**: Interactive dashboard with real-time updates
- **Software Architecture**: Modular design with clean separation of concerns
- **Financial Analysis**: Categorization, cash flow tracking, net worth calculation
- **User Experience**: Intuitive interface with detailed debugging information

## Troubleshooting

**CSV Upload Issues:**
- Check debug output for column detection results
- Ensure CSV has date, description, and amount (or debit/credit) columns
- System shows sample values before/after currency cleaning

**Date Format Errors:**
- System handles mixed date formats automatically
- Uses pandas 'mixed' format detection for compatibility

**Balance Not Updating:**
- Check that CSV has 'Balance' column
- System uses first row balance (assumes newest-first sorting)
- Manual update available for investment accounts

## Future Enhancements

- Budget tracking with alerts
- Bank-specific CSV parsers
- Data export functionality
- Multi-user support with authentication
- Historical account balance tracking
- Advanced spending analytics

This project demonstrates practical application of data engineering principles in personal finance management.