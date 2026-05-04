"""
Sample data generation for testing the finance tracker
"""
import pandas as pd
import random
from datetime import datetime, date, timedelta
from database import FinanceDB

def generate_sample_data(db: FinanceDB, num_days: int = 90):
    """create realistic fake financial data for testing/demo purposes"""
    
    # check if we already have a bunch of data - no need to add more
    existing_data = db.load_transactions()
    if len(existing_data) > 50:
        print("Sample data already exists")
        return
    
    print("Generating sample data...")
    
    # start from 3 months ago
    base_date = date.today() - timedelta(days=num_days)
    
    # wipe out any existing data for a fresh start
    import sqlite3
    conn = sqlite3.connect(db.db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transactions")
    cursor.execute("DELETE FROM accounts")
    conn.commit()
    conn.close()
    
    # build up a realistic transaction history
    transactions = []
    
    # regular paycheck every 2 weeks
    for week in range(0, num_days // 7, 2):
        pay_date = base_date + timedelta(days=week * 7)
        transactions.append({
            'date': pay_date,
            'description': 'Biweekly Paycheck - Direct Deposit',
            'amount': 1200.00,
            'category': 'Income',
            'account': 'Checking',
            'transaction_type': 'income'
        })
    
    # monthly automatic investments (20% of income each)
    for month in range(num_days // 30):
        invest_date = base_date + timedelta(days=month * 30 + 15)
        
        # to brokerage account
        transactions.append({
            'date': invest_date,
            'description': 'Investment Transfer to Brokerage',
            'amount': -480.00,  # 20% of monthly income
            'category': 'Investment',
            'account': 'Checking',
            'transaction_type': 'transfer'
        })
        
        # to roth ira
        transactions.append({
            'date': invest_date,
            'description': 'IRA Contribution',
            'amount': -480.00,
            'category': 'Investment',
            'account': 'Checking',
            'transaction_type': 'transfer'
        })
        
        # to money market savings
        transactions.append({
            'date': invest_date,
            'description': 'Savings Transfer',
            'amount': -480.00,
            'category': 'Investment',
            'account': 'Checking',
            'transaction_type': 'transfer'
        })
    
    # daily expenses with realistic spending patterns
    expense_patterns = [
        ('Kroger Grocery Store', -45, -85, 'Food', 0.15),  # 15% chance per day
        ('Shell Gas Station', -35, -55, 'Transportation', 0.05),  # gas every few weeks
        ('Amazon Purchase', -15, -120, 'Shopping', 0.08),  # online shopping addiction
        ('Starbucks Coffee', -4, -8, 'Food', 0.25),  # daily coffee habit
        ('Local Restaurant', -25, -65, 'Food', 0.12),  # eating out
        ('CVS Pharmacy', -12, -35, 'Healthcare', 0.03),  # occasional pharmacy runs
        ('Target Store', -20, -80, 'Shopping', 0.06),  # target runs
        ('Netflix Subscription', -15.99, -15.99, 'Entertainment', 0.033),  # monthly subscription
        ('Spotify Premium', -9.99, -9.99, 'Entertainment', 0.033),  # monthly music
        ('Electric Bill', -85, -125, 'Utilities', 0.033),  # monthly utility
        ('Internet Bill', -79.99, -79.99, 'Utilities', 0.033),  # monthly internet
    ]
    
    # generate daily expenses based on probabilities
    for day in range(num_days):
        current_date = base_date + timedelta(days=day)
        
        for expense_name, min_amt, max_amt, category, daily_prob in expense_patterns:
            if random.random() < daily_prob:
                amount = random.uniform(min_amt, max_amt)
                # mix of checking and credit card usage
                account = random.choice(['Checking', 'Credit Card 1', 'Credit Card 2'])
                
                transactions.append({
                    'date': current_date,
                    'description': expense_name,
                    'amount': round(amount, 2),
                    'category': category,
                    'account': account,
                    'transaction_type': 'expense'
                })
    
    # monthly credit card payments
    for month in range(num_days // 30):
        payment_date = base_date + timedelta(days=month * 30 + 25)
        
        # pay off credit card balances
        transactions.append({
            'date': payment_date,
            'description': 'Credit Card 1 Payment',
            'amount': -250.00,
            'category': 'Transfer',
            'account': 'Checking',
            'transaction_type': 'transfer'
        })
        
        transactions.append({
            'date': payment_date,
            'description': 'Credit Card 2 Payment',
            'amount': -150.00,
            'category': 'Transfer',
            'account': 'Checking',
            'transaction_type': 'transfer'
        })
    
    # occasional crypto purchases because why not
    crypto_dates = random.sample(
        [base_date + timedelta(days=d) for d in range(num_days)], 
        min(5, num_days // 20)  # about 5 crypto purchases over the period
    )
    
    for crypto_date in crypto_dates:
        amount = random.uniform(50, 200)
        transactions.append({
            'date': crypto_date,
            'description': 'Crypto Purchase',
            'amount': -round(amount, 2),
            'category': 'Investment',
            'account': 'Checking',
            'transaction_type': 'transfer'
        })
    
    # save all the transactions to database
    df = pd.DataFrame(transactions)
    rows_added = db.save_transactions(df, "Sample Data Generator")
    
    # create realistic account balances
    accounts_data = [
        ('Checking', 'Checking', 1930.00, 2000.00),  # current balance, target balance
        ('Money Market', 'Savings', 5234.67, 5000.00),
        ('Credit Card 1', 'Credit', -287.45, 0.00),  # negative balance = debt
        ('Credit Card 2', 'Credit', -156.89, 0.00),
        ('Fidelity Brokerage', 'Investment', 3567.89, 5000.00),
        ('Fidelity Roth IRA', 'Investment', 9123.45, 10000.00),
        ('Fidelity Crypto', 'Investment', 678.23, 1000.00),
    ]
    
    # add all the accounts to database
    for account_name, account_type, balance, target in accounts_data:
        db.update_account_balance(account_name, balance, account_type)
    
    print(f"Generated {rows_added} sample transactions and 7 accounts")

if __name__ == "__main__":
    # test the sample data generation if run directly
    db = FinanceDB("test_finance.db")
    generate_sample_data(db)
    
    # verify everything worked
    transactions = db.load_transactions()
    accounts = db.load_accounts()
    
    print(f"\nVerification:")
    print(f"Transactions: {len(transactions)}")
    print(f"Accounts: {len(accounts)}")
    if not transactions.empty:
        print(f"Date range: {transactions['date'].min()} to {transactions['date'].max()}")
    else:
        print("No transactions generated")