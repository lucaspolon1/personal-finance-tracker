"""
Database operations for personal finance tracker
"""
import sqlite3
import pandas as pd
from datetime import datetime
from typing import Optional, List, Dict

class FinanceDB:
    def __init__(self, db_path: str = 'finance.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """set up the database tables if they don't exist"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            print(f"Initializing database at: {self.db_path}")
            
            # main transactions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    description TEXT NOT NULL,
                    amount REAL NOT NULL,
                    category TEXT,
                    account TEXT NOT NULL,
                    transaction_type TEXT,
                    source_file TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            print("Created transactions table")
            
            # accounts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_name TEXT UNIQUE NOT NULL,
                    account_type TEXT,
                    current_balance REAL DEFAULT 0,
                    target_balance REAL DEFAULT 0,
                    last_updated DATE
                )
            ''')
            print("Created accounts table")
            
            # budget table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS budgets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    monthly_target REAL NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(category)
                )
            ''')
            print("Created budgets table")
            
            # income sources table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS income_sources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_name TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    expected_monthly REAL NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(source_name)
                )
            ''')
            print("Created income_sources table")
            
            # allocations table with new schema
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS allocations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    allocation_name TEXT NOT NULL,
                    allocation_type TEXT NOT NULL,
                    amount REAL NOT NULL,
                    priority INTEGER NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    UNIQUE(allocation_name)
                )
            ''')
            print("Created allocations table")
            
            conn.commit()
            conn.close()
            print("Database initialization completed successfully")
            
        except Exception as e:
            print(f"Database initialization failed: {e}")
            raise e
        
    def save_income_source(self, source_name: str, source_type: str, expected_monthly: float):
        """save or update an income source"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO income_sources (source_name, source_type, expected_monthly, is_active)
            VALUES (?, ?, ?, 1)
        ''', (source_name, source_type, expected_monthly))
        
        conn.commit()
        conn.close()
    
    def save_allocation(self, allocation_name: str, allocation_type: str, amount: float, priority: int):
        """save allocation - either percentage or fixed dollar amount"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # check if the table has the new schema or old schema
        cursor.execute("PRAGMA table_info(allocations)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'allocation_type' in columns and 'amount' in columns:
            # new schema
            cursor.execute('''
                INSERT OR REPLACE INTO allocations (allocation_name, allocation_type, amount, priority, is_active)
                VALUES (?, ?, ?, ?, 1)
            ''', (allocation_name, allocation_type, amount, priority))
        else:
            # old schema - store differently to avoid confusion
            # for now, just store the raw amount and handle the type logic in load
            cursor.execute('''
                INSERT OR REPLACE INTO allocations (allocation_name, percentage, priority, is_active)
                VALUES (?, ?, ?, 1)
            ''', (allocation_name, amount, priority))
            
            # store allocation type in a separate simple way
            if allocation_type == 'fixed_dollar':
                # mark dollar amounts with negative priority to distinguish them
                cursor.execute('''
                    UPDATE allocations SET priority = ? WHERE allocation_name = ?
                ''', (-priority, allocation_name))
        
        conn.commit()
        conn.close()
    
    def load_income_sources(self) -> pd.DataFrame:
        """get all active income sources"""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql("SELECT * FROM income_sources WHERE is_active = 1", conn)
        conn.close()
        return df
    
    def load_allocations(self) -> pd.DataFrame:
        """get income allocation amounts"""
        conn = sqlite3.connect(self.db_path)
        
        try:
            # try new schema first
            df = pd.read_sql("SELECT * FROM allocations WHERE is_active = 1 ORDER BY priority", conn)
            
            # check if we're using old schema and need to rename columns
            if 'percentage' in df.columns and 'amount' not in df.columns:
                df['amount'] = df['percentage']  # create amount column from percentage
                df['allocation_type'] = 'percentage'  # assume all old allocations were percentages
                
        except Exception:
            # if query fails, return empty dataframe
            df = pd.DataFrame(columns=['allocation_name', 'amount', 'allocation_type', 'priority'])
        
        conn.close()
        return df

    
    def get_income_analysis(self, year: int, month: int) -> dict:
        """analyze actual vs expected income for a month"""
        conn = sqlite3.connect(self.db_path)
        
        # get actual income from transactions
        actual_query = '''
            SELECT SUM(amount) as actual_income
            FROM transactions 
            WHERE transaction_type = 'income' 
            AND strftime('%Y', date) = ? 
            AND strftime('%m', date) = ?
        '''
        
        actual_result = pd.read_sql(actual_query, conn, params=[str(year), f"{month:02d}"])
        actual_income = actual_result['actual_income'].iloc[0] if not actual_result.empty else 0
        actual_income = actual_income if actual_income else 0
        
        # get expected income from sources
        expected_query = "SELECT SUM(expected_monthly) as expected FROM income_sources WHERE is_active = 1"
        expected_result = pd.read_sql(expected_query, conn)
        expected_income = expected_result['expected'].iloc[0] if not expected_result.empty else 0
        expected_income = expected_income if expected_income else 0
        
        conn.close()
        
        return {
            'actual_income': actual_income,
            'expected_income': expected_income,
            'variance': actual_income - expected_income,
            'variance_pct': (actual_income - expected_income) / expected_income * 100 if expected_income > 0 else 0
        }
    
    def calculate_allowance_remaining(self, year: int, month: int) -> dict:
        """calculate remaining allowance based on fixed costs vs actual spending"""
        try:
            # get income for the month
            income_data = self.get_income_analysis(year, month)
            actual_income = income_data['actual_income']
            
            conn = sqlite3.connect(self.db_path)
            
            # get actual expenses for the month (fixed bug - better query)
            expense_query = '''
                SELECT ABS(SUM(amount)) as total_expenses
                FROM transactions 
                WHERE transaction_type = 'expense'
                AND strftime('%Y', date) = ? 
                AND strftime('%m', date) = ?
            '''
            
            expense_result = pd.read_sql(expense_query, conn, params=[str(year), f"{month:02d}"])
            total_expenses = expense_result['total_expenses'].iloc[0] if not expense_result.empty and expense_result['total_expenses'].iloc[0] is not None else 0
            
            # get savings/investment transfers (fixed bug - better condition grouping)
            savings_query = '''
                SELECT ABS(SUM(amount)) as savings_transfers
                FROM transactions 
                WHERE transaction_type = 'transfer'
                AND (account LIKE '%Investment%' OR account LIKE '%IRA%' OR account LIKE '%Brokerage%' OR account LIKE '%Money Market%' OR account LIKE '%Crypto%')
                AND amount < 0
                AND strftime('%Y', date) = ? 
                AND strftime('%m', date) = ?
            '''
            
            savings_result = pd.read_sql(savings_query, conn, params=[str(year), f"{month:02d}"])
            savings_transfers = savings_result['savings_transfers'].iloc[0] if not savings_result.empty and savings_result['savings_transfers'].iloc[0] is not None else 0
            
            conn.close()
            
            # load allocations to calculate allowance
            allocations = self.load_allocations()
            
            planned_savings = 0
            fixed_costs_budget = 0
            groceries_budget = 0
            
            if not allocations.empty:
                for _, row in allocations.iterrows():
                    if row['allocation_type'] == 'percentage' and row['allocation_name'] == 'Savings/Investments':
                        planned_savings = actual_income * (row['amount'] / 100)
                    elif row['allocation_name'] == 'Fixed Costs':
                        fixed_costs_budget = row['amount']
                    elif row['allocation_name'] == 'Groceries/Food/Gas':
                        groceries_budget = row['amount']
            
            # calculate allowance = income - savings - fixed costs - groceries - everything else spent
            committed_spending = planned_savings + fixed_costs_budget + groceries_budget
            allowance_available = actual_income - committed_spending
            
            # how much have we spent that cuts into allowance?
            allowance_spent = max(0, total_expenses - (fixed_costs_budget + groceries_budget))
            allowance_remaining = allowance_available - allowance_spent
            
            return {
                'actual_income': actual_income,
                'total_expenses': total_expenses,
                'savings_invested': savings_transfers,
                'planned_savings': planned_savings,
                'fixed_costs_budget': fixed_costs_budget,
                'groceries_budget': groceries_budget,
                'allowance_available': allowance_available,
                'allowance_spent': allowance_spent,
                'allowance_remaining': allowance_remaining
            }
        
        except Exception as e:
            print(f"Error in calculate_allowance_remaining: {e}")
            # return safe defaults if something goes wrong
            return {
                'actual_income': 0,
                'total_expenses': 0,
                'savings_transfers': 0,
                'planned_savings': 0,
                'fixed_costs_budget': 0,
                'groceries_budget': 0,
                'allowance_available': 0,
                'allowance_spent': 0,
                'allowance_remaining': 0
            }
    
    def save_budget(self, category: str, monthly_target: float):
        """save or update a budget target for a category"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO budgets (category, monthly_target, is_active)
            VALUES (?, ?, 1)
        ''', (category, monthly_target))
        
        conn.commit()
        conn.close()
    
    def load_budgets(self) -> pd.DataFrame:
        """get all active budget targets"""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql("SELECT * FROM budgets WHERE is_active = 1", conn)
        conn.close()
        return df
    
    def get_budget_vs_actual(self, year: int, month: int) -> pd.DataFrame:
        """compare budget targets vs actual spending for a specific month"""
        # get actual spending for the month
        conn = sqlite3.connect(self.db_path)
        
        actual_query = '''
            SELECT category, ABS(SUM(amount)) as actual_spent
            FROM transactions 
            WHERE transaction_type = 'expense' 
            AND strftime('%Y', date) = ? 
            AND strftime('%m', date) = ?
            GROUP BY category
        '''
        
        actual_df = pd.read_sql(actual_query, conn, params=[str(year), f"{month:02d}"])
        
        # get budget targets
        budget_df = pd.read_sql("SELECT category, monthly_target FROM budgets WHERE is_active = 1", conn)
        
        conn.close()
        
        # merge budget and actual data
        if budget_df.empty:
            return pd.DataFrame()
        
        comparison = budget_df.merge(actual_df, on='category', how='left')
        comparison['actual_spent'] = comparison['actual_spent'].fillna(0)
        comparison['variance'] = comparison['actual_spent'] - comparison['monthly_target']
        comparison['variance_pct'] = (comparison['variance'] / comparison['monthly_target'] * 100).round(1)
        comparison['status'] = comparison['variance_pct'].apply(
            lambda x: 'over' if x > 10 else 'warning' if x > -10 else 'under'
        )
        
        return comparison
    
    def save_transactions(self, transactions_df: pd.DataFrame, source_file: str = "Manual") -> int:
        """basic transaction save - doesn't check for duplicates"""
        conn = sqlite3.connect(self.db_path)
        
        # add some metadata to track where data came from
        transactions_df = transactions_df.copy()
        transactions_df['source_file'] = source_file
        transactions_df['created_at'] = datetime.now()
        
        # dump everything into the database
        rows_added = len(transactions_df)
        transactions_df.to_sql('transactions', conn, if_exists='append', index=False)
        
        conn.close()
        return rows_added
    
    def load_transactions(self) -> pd.DataFrame:
        """get all transactions from database, newest first"""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql("SELECT * FROM transactions ORDER BY date DESC", conn)
        conn.close()
        
        if not df.empty:
            # handle weird date formats that might be in the database
            df['date'] = pd.to_datetime(df['date'], errors='coerce', format='mixed')
        return df
    
    def load_accounts(self) -> pd.DataFrame:
        """get all account balances"""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql("SELECT * FROM accounts", conn)
        conn.close()
        return df
    
    def update_account_balance(self, account_name: str, balance: float, account_type: str = 'Unknown'):
        """update or create an account balance entry"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # sqlite upsert - updates if exists, inserts if not
        cursor.execute('''
            INSERT OR REPLACE INTO accounts 
            (account_name, account_type, current_balance, last_updated)
            VALUES (?, ?, ?, ?)
        ''', (account_name, account_type, balance, datetime.now().date()))
        
        conn.commit()
        conn.close()
    
    def get_transactions_by_account(self, account_name: str) -> pd.DataFrame:
        """get transactions for just one specific account"""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql(
            "SELECT * FROM transactions WHERE account = ? ORDER BY date DESC", 
            conn, 
            params=[account_name]
        )
        conn.close()
        
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
        return df
    
    def transaction_exists(self, date, description, amount, account):
        """check if we've already seen this exact transaction before"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # convert date to string format for comparison
        date_str = date.strftime('%Y-%m-%d')
        
        # use DATE() function to compare just the date part, ignoring time
        cursor.execute('''
            SELECT COUNT(*) FROM transactions 
            WHERE DATE(date) = ? AND description = ? AND amount = ? AND account = ?
        ''', (date_str, description, amount, account))
        
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0
    
    def save_transactions_no_duplicates(self, transactions_df: pd.DataFrame, source_file: str = "Manual") -> tuple:
        """smart save that skips transactions we've already imported"""
        conn = sqlite3.connect(self.db_path)
        
        # go through each transaction and check if it's new
        new_transactions = []
        duplicates_found = 0
        
        for _, row in transactions_df.iterrows():
            if not self.transaction_exists(row['date'], row['description'], row['amount'], row['account']):
                new_transactions.append(row)
            else:
                duplicates_found += 1
        
        # only save the new stuff
        if new_transactions:
            new_df = pd.DataFrame(new_transactions)
            new_df['source_file'] = source_file
            new_df['created_at'] = datetime.now()
            new_df.to_sql('transactions', conn, if_exists='append', index=False)
        
        conn.close()
        return len(new_transactions), duplicates_found