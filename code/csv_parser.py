"""
CSV parsing utilities for different bank formats
Updated to handle Fidelity investment account format
"""
import pandas as pd
import re
from typing import Dict, List, Optional
from datetime import datetime

class CSVParser:
    """Handles parsing CSV files from different financial institutions"""
    
    def __init__(self):
        self.column_mappings = {
            'date': ['date', 'transaction date', 'posted date', 'trans date', 'posting date', 'effective date', 'run date'],
            'description': ['action', 'description', 'desc', 'merchant', 'payee', 'transaction description', 'memo'],  # Added 'action' as first choice
            'amount': ['amount', 'transaction amount', 'value', 'balance change', 'amount ($)']  # Added 'amount ($)' for Fidelity
        }
    
    def clean_currency_string(self, value: str) -> str:
        """Clean currency formatting from string values"""
        if pd.isna(value) or value == '':
            return '0'
        
        # Convert to string and strip whitespace
        clean_value = str(value).strip()
        
        # Handle empty or null values
        if clean_value.lower() in ['nan', 'none', '', 'null']:
            return '0'
        
        # Remove currency symbols ($, €, £, etc.)
        clean_value = re.sub(r'[$€£¥]', '', clean_value)
        
        # Remove commas and spaces
        clean_value = re.sub(r'[,\s]', '', clean_value)
        
        # Handle parentheses for negative numbers (accounting format)
        if clean_value.startswith('(') and clean_value.endswith(')'):
            clean_value = '-' + clean_value[1:-1]
        
        # Remove any remaining non-numeric characters except decimal point and minus sign
        clean_value = re.sub(r'[^\d.-]', '', clean_value)
        
        # Ensure we have a valid number
        if clean_value == '' or clean_value == '-':
            return '0'
        
        return clean_value
    
    def find_column(self, df: pd.DataFrame, column_type: str) -> Optional[str]:
        """Find the best matching column for a given type"""
        df_columns = [col.lower().strip() for col in df.columns]
        
        # First try exact matches
        for candidate in self.column_mappings[column_type]:
            if candidate in df_columns:
                return df.columns[df_columns.index(candidate)]
        
        # Then try partial matches
        for candidate in self.column_mappings[column_type]:
            for col in df.columns:
                if candidate in col.lower():
                    return col
        
        return None
    
    def categorize_transaction(self, description: str) -> str:
        """try to guess what category a transaction belongs to based on keywords"""
        if pd.isna(description):
            return 'Other'
        
        description_lower = str(description).lower()
        
        # Fidelity-specific categorization first
        if 'direct deposit' in description_lower:
            return 'Income'
        if 'dividend received' in description_lower:
            return 'Income'
        if 'electronic funds transfer received' in description_lower:
            return 'Income'
        if 'other credit' in description_lower and 'transfer' in description_lower:
            return 'Transfer'
        
        # check for credit card payments first (before utilities)
        if any(keyword in description_lower for keyword in ['credit card payment', 'cc payment', 'card payment']):
            return 'Transfer'
        
        categories = {
            'Food': ['grocery', 'restaurant', 'food', 'starbucks', 'coffee', 'pizza', 'burger', 'subway', 'mcdonald'],
            'Transportation': ['gas', 'fuel', 'uber', 'lyft', 'parking', 'metro', 'bus', 'taxi', 'car wash'],
            'Shopping': ['amazon', 'target', 'walmart', 'store', 'shop', 'retail', 'clothing', 'electronics'],
            'Utilities': ['electric', 'gas bill', 'water', 'internet', 'phone', 'cable', 'utility'],
            'Entertainment': ['netflix', 'spotify', 'movie', 'theater', 'game', 'entertainment', 'subscription'],
            'Healthcare': ['pharmacy', 'doctor', 'medical', 'hospital', 'health', 'cvs', 'walgreens'],
            'Income': ['paycheck', 'salary', 'wages', 'deposit', 'refund', 'scholarship'],
            'Investment': ['brokerage', 'investment', 'ira', 'roth', 'crypto', 'bitcoin'],
            'Transfer': ['transfer', 'withdrawal', 'deposit to', 'from savings'],
            'ATM': ['atm', 'cash withdrawal', 'fee'],
        }
        
        for category, keywords in categories.items():
            if any(keyword in description_lower for keyword in keywords):
                return category
        
        return 'Other'
    
    def determine_transaction_type(self, row) -> str:
        """Determine transaction type based on amount and category"""
        amount = row['amount']
        category = row['category']
        account = row['account']
        description = str(row['description']).lower()
        
        # Fidelity investment account logic
        if any(fidelity_word in account.lower() for fidelity_word in ['fidelity', 'brokerage', 'ira', 'roth']):
            # Direct deposits and dividends are income
            if amount > 0 and ('direct deposit' in description or 'dividend' in description or 'electronic funds transfer received' in description):
                return 'income'
            # Transfers between Fidelity accounts
            elif 'transfer' in description and ('crypto' in description or 'other credit' in description):
                return 'transfer'
            # Other positive amounts in investment accounts are likely income/deposits
            elif amount > 0:
                return 'income'
            # Negative amounts are transfers out or expenses
            else:
                return 'transfer'
        
        # Money market transactions are typically transfers/savings, not expenses
        if 'money market' in account.lower():
            if amount > 0:
                return 'transfer'  # Money going into savings
            else:
                return 'transfer'  # Money coming out of savings
        
        # Standard logic for other accounts
        if amount > 0 and category == 'Income':
            return 'income'
        elif category in ['Investment', 'Transfer']:
            return 'transfer'
        else:
            return 'expense'
    
    def parse_csv(self, file_path_or_df, account_name: str) -> pd.DataFrame:
        """Parse CSV file and return standardized DataFrame"""
        # Load data
        if isinstance(file_path_or_df, str):
            df = pd.read_csv(file_path_or_df)
        else:
            df = file_path_or_df.copy()
        
        if df.empty:
            raise ValueError("CSV file is empty")
        
        # Find required columns
        date_col = self.find_column(df, 'date')
        desc_col = self.find_column(df, 'description')
        amount_col = self.find_column(df, 'amount')
        
        # Handle case where there's no description column
        if not desc_col:
            # Look for Transaction Type or similar
            transaction_type_cols = ['transaction type', 'type', 'trans type']
            for col in df.columns:
                if any(tc in col.lower() for tc in transaction_type_cols):
                    desc_col = col
                    break
            
            # If still no description column, create one
            if not desc_col:
                df = df.copy()
                df.loc[:, 'Generated Description'] = account_name + ' Transaction'
                desc_col = 'Generated Description'
        
        # For money market accounts, check if we need to combine Debit/Credit columns
        if not amount_col:
            debit_exists = any('debit' in col.lower() for col in df.columns)
            credit_exists = any('credit' in col.lower() for col in df.columns)
            
            if debit_exists and credit_exists:
                debit_col = next(col for col in df.columns if 'debit' in col.lower())
                credit_col = next(col for col in df.columns if 'credit' in col.lower())
                
                print(f"Found separate Debit ({debit_col}) and Credit ({credit_col}) columns")
                
                # Clean both columns before combining
                debit_clean = df[debit_col].apply(self.clean_currency_string).replace('0', 0)
                credit_clean = df[credit_col].apply(self.clean_currency_string).replace('0', 0)
                
                # Convert to numeric
                debit_numeric = pd.to_numeric(debit_clean, errors='coerce').fillna(0)
                credit_numeric = pd.to_numeric(credit_clean, errors='coerce').fillna(0)
                
                # Combine: Credits are positive, Debits are negative
                df = df.copy()
                df.loc[:, 'Combined Amount'] = credit_numeric - debit_numeric       
                amount_col = 'Combined Amount'
                
                print(f"Sample combined amounts: {df[amount_col].head(3).tolist()}")
        
        # Report what we found
        print(f"Column mapping for {account_name}:")
        print(f"  Date column: {date_col}")
        print(f"  Description column: {desc_col}")
        print(f"  Amount column: {amount_col}")
        
        # Validate required columns
        missing_columns = []
        if not date_col:
            missing_columns.append('date')
        if not desc_col:
            missing_columns.append('description')
        if not amount_col:
            missing_columns.append('amount')
        
        if missing_columns:
            available_cols = list(df.columns)
            raise ValueError(
                f"Missing required columns: {missing_columns}. "
                f"Available columns: {available_cols}"
            )
        
        # Clean and convert amount column
        print(f"Sample amount values before cleaning: {df[amount_col].head(3).tolist()}")
        
        amount_series = df[amount_col].apply(self.clean_currency_string)
        print(f"Sample amount values after cleaning: {amount_series.head(3).tolist()}")
        
        # Convert to numeric
        try:
            amount_numeric = pd.to_numeric(amount_series, errors='coerce')
        except Exception as e:
            raise ValueError(f"Failed to convert amounts to numeric: {str(e)}")
        
        # Create standardized DataFrame
        parsed_df = pd.DataFrame({
            'date': pd.to_datetime(df[date_col], errors='coerce', format='mixed'),
            'description': df[desc_col].astype(str).str.strip(),
            'amount': amount_numeric,
            'account': account_name
        })
        
        # Remove rows with missing critical data
        before_count = len(parsed_df)
        parsed_df = parsed_df.dropna(subset=['date', 'description', 'amount'])
        after_count = len(parsed_df)
        
        if before_count != after_count:
            print(f"Removed {before_count - after_count} rows with missing data")
        
        # Add categories and transaction types
        parsed_df['category'] = parsed_df['description'].apply(self.categorize_transaction)
        parsed_df['transaction_type'] = parsed_df.apply(self.determine_transaction_type, axis=1)
        
        return parsed_df

# Factory function for easy usage
def parse_bank_csv(file_path_or_df, account_name: str) -> pd.DataFrame:
    """Convenience function to parse bank CSV"""
    parser = CSVParser()
    return parser.parse_csv(file_path_or_df, account_name)