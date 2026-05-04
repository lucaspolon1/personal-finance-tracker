"""
Personal Finance Tracker - Main Application
Run with: streamlit run main.py
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# bring in our custom modules
from database import FinanceDB
from csv_parser import parse_bank_csv
from sample_data import generate_sample_data

# basic page setup
st.set_page_config(
    page_title="Personal Finance Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# theme selector in sidebar
if 'theme' not in st.session_state:
    st.session_state.theme = 'Dark (SCADA)'

# put theme selector at the top of sidebar
with st.sidebar:
    st.session_state.theme = st.selectbox(
        "🎨 Theme",
        ["Light", "Dark (SCADA)", "Wall Street"],
        index=["Light", "Dark (SCADA)", "Wall Street"].index(st.session_state.theme)
    )

# apply theme-specific css
def apply_theme(theme_name):
    if theme_name == "Light":
        return """
        <style>
            .stApp {
                background-color: #ffffff;
                color: #000000;
            }
            .metric-card {
                background: linear-gradient(135deg, #f0f0f0 0%, #e0e0e0 100%);
                padding: 1rem;
                border-radius: 10px;
                border-left: 5px solid #2196F3;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            }
            .alert-good { color: #4CAF50; font-weight: bold; }
            .alert-warning { color: #FF9800; font-weight: bold; }
            .alert-bad { color: #F44336; font-weight: bold; }
        </style>
        """
    
    elif theme_name == "Dark (SCADA)":
        return """
        <style>
            /* complete dark mode override */
            .stApp {
                background-color: #000000 !important;
                color: #00ff88 !important;
            }
            
            /* fix sidebar */
            .css-1d391kg, .css-1cypcdb, .css-17lntkn {
                background-color: #111111 !important;
            }
            
            /* fix main content area */
            .main .block-container {
                background-color: #000000 !important;
            }
            
            /* fix header/toolbar */
            .css-18e3th9, .css-1avcm0n {
                background-color: #111111 !important;
            }
            
            /* metric cards with SCADA styling */
            .metric-card {
                background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
                padding: 1rem;
                border-radius: 10px;
                border-left: 5px solid #00ff88;
                border: 1px solid #333333;
                box-shadow: 0 0 10px rgba(0, 255, 136, 0.2);
            }
            
            /* SCADA-style status colors */
            .alert-good { color: #00ff88; font-weight: bold; text-shadow: 0 0 5px #00ff88; }
            .alert-warning { color: #ffaa00; font-weight: bold; text-shadow: 0 0 5px #ffaa00; }
            .alert-bad { color: #ff4444; font-weight: bold; text-shadow: 0 0 5px #ff4444; }
            
            /* metric values in lime green */
            [data-testid="metric-container"] {
                background-color: #1a1a1a;
                border: 1px solid #333333;
                border-radius: 5px;
                padding: 10px;
            }
            
            [data-testid="metric-container"] > div {
                color: #00ff88 !important;
            }
            
            /* dataframes dark styling */
            .stDataFrame {
                background-color: #1a1a1a !important;
                border: 1px solid #333333;
            }
            
            /* buttons */
            .stButton > button {
                background-color: #2a5298;
                color: #00ff88;
                border: 1px solid #00ff88;
                border-radius: 5px;
            }
            
            .stButton > button:hover {
                background-color: #00ff88;
                color: #000000;
                box-shadow: 0 0 10px rgba(0, 255, 136, 0.5);
            }
            
            /* selectboxes and inputs */
            .stSelectbox > div > div, .stNumberInput > div > div {
                background-color: #1a1a1a !important;
                color: #00ff88 !important;
                border: 1px solid #333333;
            }
            
            /* text elements */
            h1, h2, h3, .stMarkdown {
                color: #00ff88 !important;
            }
            
            /* plotly charts dark background */
            .js-plotly-plot {
                background-color: #000000 !important;
            }
        </style>
        """
    
    elif theme_name == "Wall Street":
        return """
        <style>
            /* wall street theme - sophisticated dark with gold accents */
            .stApp {
                background: linear-gradient(180deg, #0a0e1a 0%, #1a1f2e 100%);
                color: #d4af37;
            }
            
            /* sidebar styling */
            .css-1d391kg, .css-1cypcdb, .css-17lntkn {
                background: linear-gradient(180deg, #1a1f2e 0%, #0f1419 100%) !important;
                border-right: 2px solid #d4af37;
            }
            
            /* main content */
            .main .block-container {
                background: transparent;
            }
            
            /* header */
            .css-18e3th9, .css-1avcm0n {
                background: linear-gradient(90deg, #0a0e1a 0%, #1a1f2e 100%) !important;
                border-bottom: 1px solid #d4af37;
            }
            
            /* metric cards - professional trading terminal style */
            .metric-card {
                background: linear-gradient(135deg, #1a1f2e 0%, #252b3d 100%);
                padding: 1rem;
                border-radius: 8px;
                border: 2px solid #d4af37;
                box-shadow: 0 4px 8px rgba(212, 175, 55, 0.1),
                           inset 0 1px 0 rgba(255, 255, 255, 0.1);
            }
            
            /* wall street status colors */
            .alert-good { color: #00c851; font-weight: bold; text-shadow: 0 0 8px #00c851; }
            .alert-warning { color: #d4af37; font-weight: bold; text-shadow: 0 0 8px #d4af37; }
            .alert-bad { color: #ff3547; font-weight: bold; text-shadow: 0 0 8px #ff3547; }
            
            /* metrics styling */
            [data-testid="metric-container"] {
                background: linear-gradient(135deg, #252b3d 0%, #1a1f2e 100%);
                border: 1px solid #d4af37;
                border-radius: 8px;
                padding: 15px;
                box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.3);
            }
            
            [data-testid="metric-container"] > div {
                color: #d4af37 !important;
                font-family: 'Courier New', monospace;
            }
            
            /* dataframes */
            .stDataFrame {
                background: linear-gradient(135deg, #1a1f2e 0%, #252b3d 100%);
                border: 2px solid #d4af37;
                border-radius: 8px;
            }
            
            /* buttons */
            .stButton > button {
                background: linear-gradient(135deg, #d4af37 0%, #b8941f 100%);
                color: #0a0e1a;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                box-shadow: 0 2px 4px rgba(212, 175, 55, 0.3);
            }
            
            .stButton > button:hover {
                background: linear-gradient(135deg, #f0c14b 0%, #d4af37 100%);
                box-shadow: 0 4px 8px rgba(212, 175, 55, 0.4);
                transform: translateY(-1px);
            }
            
            /* inputs */
            .stSelectbox > div > div, .stNumberInput > div > div {
                background: linear-gradient(135deg, #252b3d 0%, #1a1f2e 100%) !important;
                color: #d4af37 !important;
                border: 1px solid #d4af37;
                font-family: 'Courier New', monospace;
            }
            
            /* headings */
            h1 {
                color: #d4af37 !important;
                text-shadow: 0 0 10px rgba(212, 175, 55, 0.5);
                font-family: 'Times New Roman', serif;
            }
            
            h2, h3 {
                color: #f0c14b !important;
                font-family: 'Times New Roman', serif;
            }
            
            /* general text */
            .stMarkdown {
                color: #d4af37 !important;
            }
        </style>
        """

# apply the selected theme
st.markdown(apply_theme(st.session_state.theme), unsafe_allow_html=True)

# set up database connection with caching so we don't keep reconnecting
def init_db():
    return FinanceDB()

def calculate_financial_metrics(transactions, accounts):
    """figure out all the important money numbers"""
    # handle empty accounts gracefully 
    if accounts.empty:
        return {'net_worth': 0, 'total_assets': 0, 'total_debt': 0, 
                'monthly_expenses': 0, 'monthly_income': 0}
    
    # basic net worth calculation
    total_assets = accounts[accounts['current_balance'] > 0]['current_balance'].sum()
    total_debt = abs(accounts[accounts['current_balance'] < 0]['current_balance'].sum())
    net_worth = total_assets - total_debt
    
    # cash flow for the last month
    if not transactions.empty:
        last_30_days = datetime.now() - timedelta(days=30)
        recent_transactions = transactions[transactions['date'] >= last_30_days]
        
        # sum up all the money going out
        monthly_expenses = abs(recent_transactions[
            recent_transactions['transaction_type'] == 'expense'
        ]['amount'].sum())
        
        # sum up money coming in (including money market deposits as "income")
        monthly_income = recent_transactions[
            (recent_transactions['transaction_type'] == 'income') |
            ((recent_transactions['transaction_type'] == 'transfer') & 
            (recent_transactions['account'] == 'Money Market') & 
            (recent_transactions['amount'] > 0))
        ]['amount'].sum()
    else:
        # no transactions yet
        monthly_expenses = 0
        monthly_income = 0
    
    return {
        'net_worth': net_worth,
        'total_assets': total_assets,
        'total_debt': total_debt,
        'monthly_expenses': monthly_expenses,
        'monthly_income': monthly_income
    }

def main():
    """main app controller - routes to different pages"""
    db = init_db()
    
    # sidebar navigation menu
    st.sidebar.title("🎛️ Finance Tracker")
    page = st.sidebar.selectbox("Navigate", ["Dashboard", "Income", "Budget", "Upload Data", "Transactions", "Analysis"])
    
    # route to the right page
    if page == "Dashboard":
        dashboard_page(db)
    elif page == "Income":
        income_page(db)
    elif page == "Budget":
        budget_page(db)
    elif page == "Upload Data":
        upload_page(db)
    elif page == "Transactions":
        transactions_page(db)
    elif page == "Analysis":
        analysis_page(db)

def income_page(db):
    """income tracking and allowance calculation page"""
    st.title("💰 Income & Allowance Tracker")
    
    # load current data
    transactions = db.load_transactions()
    income_sources = db.load_income_sources()
    allocations = db.load_allocations()
    
    # current month for analysis
    today = datetime.now()
    current_year = today.year
    current_month = today.month
    
    # month selector
    col1, col2 = st.columns(2)
    with col1:
        selected_year = st.selectbox("Year:", range(current_year - 1, current_year + 2), index=1)
    with col2:
        selected_month = st.selectbox("Month:", range(1, 13), index=current_month - 1, 
                                     format_func=lambda x: datetime(2024, x, 1).strftime('%B'))
    
    # allowance status - the most important part for peace of mind
    st.subheader("Allowance Status")
    allowance_data = db.calculate_allowance_remaining(selected_year, selected_month)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Income This Month", f"${allowance_data['actual_income']:,.2f}")
    with col2:
        st.metric("Total Expenses", f"${allowance_data['total_expenses']:,.2f}")
    with col3:
        st.metric("Saved/Invested", f"${allowance_data['savings_invested']:,.2f}")
    with col4:
        remaining = allowance_data['allowance_remaining']
        color = "normal" if remaining >= 0 else "inverse"
        st.metric("Allowance Remaining", f"${remaining:,.2f}", delta_color=color)
    
    # peace of mind indicator
    if remaining >= 50:
        st.success("You have plenty of discretionary spending room this month")
    elif remaining >= 0:
        st.warning("You're getting close to your discretionary spending limit")
    else:
        st.error("You've exceeded your planned discretionary spending this month")
    
    st.divider()
    
    # income sources setup
    st.subheader("Income Sources")
    
    with st.expander("Add/Update Income Sources", expanded=len(income_sources) == 0):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            source_name = st.text_input("Income Source Name", placeholder="e.g., Part-time Job, Scholarship")
        with col2:
            source_type = st.selectbox("Type", ["salary", "scholarship", "side_hustle", "internship", "other"])
        with col3:
            expected_monthly = st.number_input("Expected Monthly ($)", min_value=0.0, step=50.0)
        
        if st.button("Save Income Source"):
            if source_name and expected_monthly > 0:
                db.save_income_source(source_name, source_type, expected_monthly)
                st.success(f"Added {source_name} with ${expected_monthly:,.2f}/month")
                st.rerun()
            else:
                st.warning("Please fill in all fields")
    
    # show current income sources
    if not income_sources.empty:
        st.subheader("Current Income Sources")
        display_sources = income_sources.copy()
        display_sources['expected_monthly'] = display_sources['expected_monthly'].apply(lambda x: f"${x:,.2f}")
        
        st.dataframe(
            display_sources[['source_name', 'source_type', 'expected_monthly']],
            column_config={
                'source_name': 'Source',
                'source_type': 'Type', 
                'expected_monthly': 'Monthly Expected'
            },
            use_container_width=True,
            hide_index=True
        )
        
        total_expected = income_sources['expected_monthly'].sum()
        st.info(f"Total Expected Monthly Income: ${total_expected:,.2f}")
    
    st.divider()
    
    # financial allocation setup - fixed dollar amounts for essentials
    st.subheader("Income Allocation Strategy")
    
    with st.expander("Set Income Allocation", expanded=len(allocations) == 0):
        st.write("Set your monthly allocations:")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # savings/investments as percentage
            current_savings_pct = 20  # default
            if not allocations.empty:
                savings_row = allocations[allocations['allocation_name'] == 'Savings/Investments']
                if not savings_row.empty:
                    current_savings_pct = savings_row['amount'].iloc[0]
            
            savings_pct = st.number_input(
                "Savings/Investments (%)",
                min_value=0.0,
                max_value=100.0,
                value=float(current_savings_pct),
                step=1.0
            )
            
            # fixed costs as dollar amount
            current_fixed = 800  # default
            if not allocations.empty:
                fixed_row = allocations[allocations['allocation_name'] == 'Fixed Costs']
                if not fixed_row.empty:
                    current_fixed = fixed_row['amount'].iloc[0]
            
            fixed_costs = st.number_input(
                "Fixed Costs ($/month)",
                min_value=0.0,
                value=float(current_fixed),
                step=50.0,
                help="Rent, utilities, insurance, subscriptions, etc."
            )
        
        with col2:
            # groceries/food/gas as dollar amount
            current_groceries = 300  # default
            if not allocations.empty:
                groceries_row = allocations[allocations['allocation_name'] == 'Groceries/Food/Gas']
                if not groceries_row.empty:
                    current_groceries = groceries_row['amount'].iloc[0]
            
            groceries_amount = st.number_input(
                "Groceries/Food/Gas ($/month)",
                min_value=0.0,
                value=float(current_groceries),
                step=25.0,
                help="Food, gas, household supplies"
            )
            
            # show calculated allowance
            if not income_sources.empty:
                total_income = income_sources['expected_monthly'].sum()
                planned_savings = total_income * (savings_pct / 100)
                remaining_for_allowance = total_income - planned_savings - fixed_costs - groceries_amount
                
                st.metric("Calculated Monthly Allowance", f"${remaining_for_allowance:,.2f}")
        
        if st.button("Save Allocation Strategy"):
            db.save_allocation('Savings/Investments', 'percentage', savings_pct, 1)
            db.save_allocation('Fixed Costs', 'fixed_dollar', fixed_costs, 2)
            db.save_allocation('Groceries/Food/Gas', 'fixed_dollar', groceries_amount, 3)
            st.success("Saved allocation strategy")
            st.rerun()
    
    # show current allocations with breakdown
    if not allocations.empty and not income_sources.empty:
        st.subheader("Current Allocation Breakdown")
        
        total_income = income_sources['expected_monthly'].sum()
        
        breakdown = []
        remaining_income = total_income
        
        for _, row in allocations.iterrows():
            if row['allocation_type'] == 'percentage':
                amount = total_income * (row['amount'] / 100)
                display = f"{row['amount']:.1f}% (${amount:,.2f})"
            else:
                amount = row['amount']
                display = f"${amount:,.2f}"
            
            breakdown.append({
                'Category': row['allocation_name'],
                'Amount': display,
                'Dollar_Amount': amount
            })
            remaining_income -= amount
        
        # add allowance as calculated remainder
        breakdown.append({
            'Category': 'Available for Discretionary',
            'Amount': f"${remaining_income:,.2f}",
            'Dollar_Amount': remaining_income
        })
        
        breakdown_df = pd.DataFrame(breakdown)
        st.dataframe(
            breakdown_df[['Category', 'Amount']],
            use_container_width=True,
            hide_index=True
        )
        
        # pie chart of allocation
        fig = px.pie(
            breakdown_df,
            values='Dollar_Amount',
            names='Category',
            title='Monthly Income Allocation'
        )
        fig.update_layout(
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='#fafafa' if st.session_state.theme != "Light" else '#000000'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # income analysis and trends
    st.subheader("📈 Income Analysis")
    
    # current month performance
    income_analysis = db.get_income_analysis(selected_year, selected_month)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # income vs expected chart
        fig = go.Figure(data=[
            go.Bar(name='Expected', x=['Income'], y=[income_analysis['expected_income']], marker_color='lightblue'),
            go.Bar(name='Actual', x=['Income'], y=[income_analysis['actual_income']], marker_color='green' if income_analysis['variance'] >= 0 else 'red')
        ])
        
        fig.update_layout(
            title=f"Income Performance - {datetime(selected_year, selected_month, 1).strftime('%B %Y')}",
            yaxis_title='Amount ($)',
            barmode='group',
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='#fafafa' if st.session_state.theme != "Light" else '#000000'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # allocation pie chart
        if not allocations.empty and not income_sources.empty:
            total_income = income_sources['expected_monthly'].sum()
            allocation_amounts = allocations.copy()
            
            # calculate actual dollar amounts based on allocation type
            allocation_amounts['dollar_amount'] = allocation_amounts.apply(
                lambda row: (total_income * row['amount'] / 100) if row['allocation_type'] == 'percentage' 
                else row['amount'], axis=1
            )
            
            fig = px.pie(
                allocation_amounts,
                values='dollar_amount',
                names='allocation_name',
                title='Planned Income Allocation'
            )
            fig.update_layout(
                height=400,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='#fafafa' if st.session_state.theme != "Light" else '#000000'
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # income trend over last 6 months
    if not transactions.empty:
        st.subheader("6-Month Income Trend")
        
        six_months_ago = datetime.now() - timedelta(days=180)
        income_transactions = transactions[
            (transactions['transaction_type'] == 'income') & 
            (transactions['date'] >= six_months_ago)
        ]
        
        if not income_transactions.empty:
            monthly_income = income_transactions.copy()
            monthly_income['month'] = monthly_income['date'].dt.to_period('M')
            monthly_totals = monthly_income.groupby('month')['amount'].sum()
            
            fig = px.line(
                x=monthly_totals.index.astype(str),
                y=monthly_totals.values,
                title='Monthly Income Trend',
                labels={'x': 'Month', 'y': 'Income ($)'}
            )
            
            # add expected income line if we have sources defined
            if not income_sources.empty:
                expected_monthly = income_sources['expected_monthly'].sum()
                fig.add_hline(
                    y=expected_monthly, 
                    line_dash="dash", 
                    line_color="orange",
                    annotation_text=f"Expected: ${expected_monthly:,.2f}/month"
                )
            
            fig.update_layout(
                height=400,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='#fafafa' if st.session_state.theme != "Light" else '#000000'
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    # financial insights and recommendations
    st.subheader("💡 Financial Insights")
    
    if allowance_data['allowance_remaining'] > 100:
        st.info("💰 You're under budget on discretionary spending - consider increasing your investment allocation or saving for travel!")
    
    if income_analysis['variance'] < -100:
        st.warning("📉 Your actual income is significantly below expected - you may want to adjust your budget or find additional income sources")
    
    if allowance_data['savings_invested'] / allowance_data['actual_income'] > 0.4:
        st.success("🚀 You're crushing your savings goals! Keep up the great work on building wealth early")

def budget_page(db):
    """budget management and tracking page"""
    st.title("📊 Budget Management")
    
    # load current data
    transactions = db.load_transactions()
    budgets = db.load_budgets()
    
    if transactions.empty:
        st.warning("No transaction data found. Upload some data first to create budgets!")
        return
    
    # get current month for budget vs actual
    today = datetime.now()
    current_year = today.year
    current_month = today.month
    
    # month selector for budget comparison
    col1, col2 = st.columns(2)
    with col1:
        selected_year = st.selectbox("Year:", range(current_year - 1, current_year + 2), index=1)
    with col2:
        selected_month = st.selectbox("Month:", range(1, 13), index=current_month - 1, 
                                     format_func=lambda x: datetime(2024, x, 1).strftime('%B'))
    
    # budget setup section
    st.subheader("Set Budget Targets")
    
    # get all categories from transactions for budget setup
    expense_transactions = transactions[transactions['transaction_type'] == 'expense']
    if not expense_transactions.empty:
        categories = sorted(expense_transactions['category'].unique())
        
        # budget input form
        with st.expander("💰 Set Monthly Budget Targets", expanded=False):
            st.write("Set spending limits for each category:")
            
            # create budget inputs in columns
            num_cols = 3
            cols = st.columns(num_cols)
            
            new_budgets = {}
            for i, category in enumerate(categories):
                col_idx = i % num_cols
                
                with cols[col_idx]:
                    # get current budget if it exists
                    current_budget = 0
                    if not budgets.empty:
                        existing = budgets[budgets['category'] == category]
                        if not existing.empty:
                            current_budget = existing['monthly_target'].iloc[0]
                    
                    # get average spending for this category as suggestion
                    avg_spending = expense_transactions[
                        expense_transactions['category'] == category
                    ]['amount'].abs().mean()
                    
                    suggested = max(current_budget, avg_spending) if current_budget > 0 else avg_spending
                    
                    budget_amount = st.number_input(
                        f"{category}",
                        min_value=0.0,
                        value=float(suggested) if suggested > 0 else 0.0,
                        step=10.0,
                        key=f"budget_{category}",
                        help=f"Avg spending: ${avg_spending:.2f}" if avg_spending > 0 else "No spending data"
                    )
                    
                    if budget_amount > 0:
                        new_budgets[category] = budget_amount
            
            # save budgets button
            if st.button("💾 Save Budget Targets"):
                if new_budgets:
                    for category, amount in new_budgets.items():
                        db.save_budget(category, amount)
                    st.success(f"Saved budgets for {len(new_budgets)} categories!")
                    st.rerun()
                else:
                    st.warning("Please set at least one budget target.")
    
    # budget vs actual comparison
    st.subheader(f"Budget Performance - {datetime(selected_year, selected_month, 1).strftime('%B %Y')}")
    
    # reload budgets after potential updates
    budgets = db.load_budgets()
    
    if budgets.empty:
        st.info("No budget targets set yet. Use the section above to create your first budget.")
        return
    
    # get budget vs actual data
    comparison = db.get_budget_vs_actual(selected_year, selected_month)
    
    if comparison.empty:
        st.info("No spending data found for the selected month.")
        return
    
    # summary metrics
    total_budgeted = comparison['monthly_target'].sum()
    total_spent = comparison['actual_spent'].sum()
    total_remaining = total_budgeted - total_spent
    overall_performance = (total_spent / total_budgeted * 100) if total_budgeted > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🎯 Total Budget", f"${total_budgeted:,.2f}")
    with col2:
        st.metric("💸 Total Spent", f"${total_spent:,.2f}")
    with col3:
        color = "normal" if total_remaining >= 0 else "inverse"
        st.metric("💰 Remaining", f"${total_remaining:,.2f}", delta_color=color)
    with col4:
        status_color = "inverse" if overall_performance > 100 else "normal"
        st.metric("📊 Budget Used", f"{overall_performance:.1f}%", delta_color=status_color)
    
    # detailed budget breakdown
    st.subheader("Category Breakdown")
    
    # visual budget performance chart
    col1, col2 = st.columns(2)
    
    with col1:
        # horizontal bar chart comparing budget vs actual
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='Budget',
            y=comparison['category'],
            x=comparison['monthly_target'],
            orientation='h',
            marker_color='lightblue',
            opacity=0.7
        ))
        
        fig.add_trace(go.Bar(
            name='Actual',
            y=comparison['category'],
            x=comparison['actual_spent'],
            orientation='h',
            marker_color=['red' if x > 0 else 'green' for x in comparison['variance']],
            opacity=0.8
        ))
        
        fig.update_layout(
            title='Budget vs Actual Spending',
            xaxis_title='Amount ($)',
            yaxis_title='Category',
            barmode='group',
            height=max(400, len(comparison) * 50),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='#fafafa'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # pie chart of budget allocation
        fig = px.pie(
            comparison,
            values='monthly_target',
            names='category',
            title='Budget Allocation by Category'
        )
        fig.update_layout(
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='#fafafa'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # detailed table with status indicators
    st.subheader("Detailed Budget Analysis")
    
    # format the data for display
    display_df = comparison.copy()
    display_df['budget'] = display_df['monthly_target'].apply(lambda x: f"${x:,.2f}")
    display_df['actual'] = display_df['actual_spent'].apply(lambda x: f"${x:,.2f}")
    display_df['variance'] = display_df['variance'].apply(lambda x: f"${x:,.2f}")
    display_df['variance_pct'] = display_df['variance_pct'].apply(lambda x: f"{x:+.1f}%")
    
    # status emoji mapping
    status_map = {
        'under': '✅ Under Budget',
        'warning': '⚠️ Close to Limit', 
        'over': '🚨 Over Budget'
    }
    display_df['status'] = display_df['status'].map(status_map)
    
    # show the table
    st.dataframe(
        display_df[['category', 'budget', 'actual', 'variance', 'variance_pct', 'status']],
        column_config={
            'category': 'Category',
            'budget': 'Budgeted',
            'actual': 'Actual Spent',
            'variance': 'Over/Under',
            'variance_pct': '% Variance',
            'status': 'Status'
        },
        use_container_width=True,
        hide_index=True
    )
    
    # budget alerts section
    over_budget = comparison[comparison['variance'] > 0]
    if not over_budget.empty:
        st.subheader("🚨 Budget Alerts")
        for _, row in over_budget.iterrows():
            st.error(f"**{row['category']}**: ${row['variance']:.2f} over budget ({row['variance_pct']:+.1f}%)")
    
    # spending trends for budgeted categories
    st.subheader("📈 Spending Trends")
    
    # get last 6 months of spending for budgeted categories
    six_months_ago = datetime.now() - timedelta(days=180)
    recent_expenses = transactions[
        (transactions['transaction_type'] == 'expense') & 
        (transactions['date'] >= six_months_ago) &
        (transactions['category'].isin(comparison['category']))
    ]
    
    if not recent_expenses.empty:
        # group by month and category
        recent_expenses['month'] = recent_expenses['date'].dt.to_period('M')
        monthly_spending = recent_expenses.groupby(['month', 'category'])['amount'].sum().abs().unstack(fill_value=0)
        
        # plot spending trends
        fig = go.Figure()
        
        for category in monthly_spending.columns:
            fig.add_trace(go.Scatter(
                x=monthly_spending.index.astype(str),
                y=monthly_spending[category],
                mode='lines+markers',
                name=category,
                line=dict(width=2)
            ))
        
        fig.update_layout(
            title='6-Month Spending Trends by Category',
            xaxis_title='Month',
            yaxis_title='Amount ($)',
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='#fafafa'
        )
        
        st.plotly_chart(fig, use_container_width=True)

def dashboard_page(db):
    """main dashboard with all the important stats and charts"""
    st.title("💰 Personal Finance Dashboard")
    
    # load all our data
    transactions = db.load_transactions()
    accounts = db.load_accounts()
    
    # create sample data if database is empty (helpful for testing)
    if transactions.empty:
        st.info("No data found. Upload your CSV files or generate sample data below.")
        if st.button("Generate Sample Data for Testing"):
            with st.spinner("Setting up sample data..."):
                generate_sample_data(db)
                transactions = db.load_transactions()
                accounts = db.load_accounts()
                st.rerun()
        return
    
    # crunch all the numbers
    metrics = calculate_financial_metrics(transactions, accounts)
    
    # top row of big important numbers
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("💎 Net Worth", f"${metrics['net_worth']:,.2f}")
    with col2:
        st.metric("💰 Total Assets", f"${metrics['total_assets']:,.2f}")
    with col3:
        st.metric("💳 Total Debt", f"${metrics['total_debt']:,.2f}")
    with col4:
        # calculate savings rate as a percentage
        savings_rate = ((metrics['monthly_income'] - metrics['monthly_expenses']) / 
                       metrics['monthly_income'] * 100) if metrics['monthly_income'] > 0 else 0
        st.metric("📊 Savings Rate", f"{savings_rate:.1f}%")
    
    st.divider()
    
    # two main charts side by side
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏦 Account Balances")
        if not accounts.empty:
            # bar chart of all account balances
            fig = px.bar(
                accounts, 
                x='account_name', 
                y='current_balance',
                color='current_balance',
                color_continuous_scale='RdYlGn',
                title="Account Balances"
            )
            # make it dark theme compatible
            fig.update_layout(
                height=400,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='#fafafa'
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("🛒 Spending by Category")
        if not transactions.empty:
            # only look at recent spending
            last_30_days = datetime.now() - timedelta(days=30)
            recent_expenses = transactions[
                (transactions['transaction_type'] == 'expense') & 
                (transactions['date'] >= last_30_days)
            ]
            
            if not recent_expenses.empty:
                # group spending by category
                category_spending = recent_expenses.groupby('category')['amount'].sum().abs()
                fig = px.pie(
                    values=category_spending.values,
                    names=category_spending.index,
                    title="Last 30 Days Spending"
                )
                # dark theme styling
                fig.update_layout(
                    height=400,
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_color='#fafafa'
                )
                st.plotly_chart(fig, use_container_width=True)
    
    # recent transaction list at the bottom
    st.subheader("📋 Recent Transactions")
    if not transactions.empty:
        recent = transactions.head(10).copy()
        # format amounts nicely
        recent['amount'] = recent['amount'].apply(lambda x: f"${x:,.2f}")
        recent['date'] = recent['date'].dt.strftime('%Y-%m-%d')
        st.dataframe(
            recent[['date', 'description', 'amount', 'category', 'account']],
            use_container_width=True
        )

def upload_page(db):
    """handle csv file uploads and manual balance updates"""
    st.title("📤 Upload Bank Data")
    
    # dropdown to pick which account
    account_options = [
        "Checking", "Money Market", "Credit Card 1", "Credit Card 2",
        "Fidelity Brokerage", "Fidelity Roth IRA", "Fidelity Crypto"
    ]
    account_name = st.selectbox("Select Account:", account_options)

    # special handling for investment accounts
    if account_name in ['Fidelity Brokerage', 'Fidelity Roth IRA', 'Fidelity Crypto']:
        st.subheader("Investment Account Balance Update")
        st.info("For investment accounts, just update the current portfolio value instead of importing transactions.")
        
        col1, col2 = st.columns(2)
        with col1:
            current_value = st.number_input(f"Current {account_name} Value ($)", min_value=0.0, step=100.0)
            
        with col2:
            if st.button(f"Update {account_name} Balance"):
                account_type = 'Investment'
                db.update_account_balance(account_name, current_value, account_type)
                st.success(f"Updated {account_name} balance to ${current_value:,.2f}")
                st.cache_data.clear()
        
        st.divider()
    
    # csv file uploader
    uploaded_file = st.file_uploader("Choose CSV file", type="csv")
    
    if uploaded_file is not None:
        try:
            # read and show a preview
            df = pd.read_csv(uploaded_file)
            
            st.subheader("📊 File Preview")
            st.dataframe(df.head())
            
            st.subheader("📋 Column Information")
            st.write("Detected columns:", list(df.columns))
            
            if st.button("🔄 Process and Import"):
                with st.spinner("Processing transactions..."):
                    try:
                        # run it through our csv parser
                        parsed_df = parse_bank_csv(df, account_name)
                        
                        st.write("Debug: Parsed data preview:")
                        st.dataframe(parsed_df.head())
                        st.write(f"Debug: Parsed {len(parsed_df)} transactions")
                        
                        # save to database (automatically skips duplicates)
                        rows_added, duplicates_skipped = db.save_transactions_no_duplicates(parsed_df, uploaded_file.name)
                        st.write(f"Debug: Added {rows_added} new transactions, skipped {duplicates_skipped} duplicates")
                        
                        # try to update account balance from csv
                        st.write(f"Debug: Checking for Balance column in {list(df.columns)}")
                        if 'Balance' in df.columns:
                            st.write(f"Debug: Balance column found with first 3 values: {df['Balance'].head(3).tolist()}")
                            st.write(f"Debug: Last 3 balance values: {df['Balance'].tail(3).tolist()}")
                            if not df['Balance'].empty:
                                # grab the first balance (assuming csv is newest-first)
                                first_balance_str = str(df['Balance'].iloc[0])
                                st.write(f"Debug: First balance string (most recent): {first_balance_str}")
                                # clean up the currency formatting
                                from csv_parser import CSVParser
                                parser = CSVParser()
                                clean_balance = parser.clean_currency_string(first_balance_str)
                                st.write(f"Debug: Clean balance: {clean_balance}")
                                latest_balance = float(clean_balance)
                                # update in database
                                db.update_account_balance(account_name, latest_balance, 'Savings')
                                st.write(f"Debug: Updated {account_name} balance to ${latest_balance:,.2f}")
                            else:
                                st.write("Debug: Balance column is empty")
                        else:
                            st.write("Debug: No Balance column found")
                        
                        # double check everything saved correctly
                        all_transactions = db.load_transactions()
                        st.write(f"Debug: Total transactions in database: {len(all_transactions)}")
                        
                        st.success(f"✅ Successfully imported {rows_added} transactions!")
                        
                        # show summary stats
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Transactions", rows_added)
                        with col2:
                            st.metric("Categories", parsed_df['category'].nunique())
                        with col3:
                            net_amount = parsed_df['amount'].sum()
                            st.metric("Net Amount", f"${net_amount:,.2f}")
                        
                        # refresh the cached data
                        st.cache_data.clear()
                    
                    except Exception as e:
                        st.error(f"Error during processing: {str(e)}")
                        import traceback
                        st.code(traceback.format_exc())
        
        except Exception as e:
            st.error(f"❌ Error processing file: {str(e)}")
            
            # show debug info when things go wrong
            if 'df' in locals():
                st.subheader("🔍 Debug Information")
                st.write("Available columns:", list(df.columns))
                st.write("First few rows:")
                st.dataframe(df.head(3))

def transactions_page(db):
    """view and filter all transactions"""
    st.title("📋 Transaction History")
    
    transactions = db.load_transactions()
    
    if transactions.empty:
        st.warning("No transactions found. Upload some data first!")
        return
    
    # filter controls across the top
    col1, col2, col3 = st.columns(3)
    
    with col1:
        accounts = ["All"] + list(transactions['account'].unique())
        selected_account = st.selectbox("Account:", accounts)
    
    with col2:
        categories = ["All"] + list(transactions['category'].unique())
        selected_category = st.selectbox("Category:", categories)
    
    with col3:
        date_range = st.date_input(
            "Date Range:",
            value=(datetime.now() - timedelta(days=30), datetime.now())
        )
    
    # apply all the filters
    filtered_df = transactions.copy()
    
    if selected_account != "All":
        filtered_df = filtered_df[filtered_df['account'] == selected_account]
    
    if selected_category != "All":
        filtered_df = filtered_df[filtered_df['category'] == selected_category]
    
    if len(date_range) == 2:
        filtered_df = filtered_df[
            (filtered_df['date'].dt.date >= date_range[0]) & 
            (filtered_df['date'].dt.date <= date_range[1])
        ]
    
    # summary metrics for filtered data
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Transactions", len(filtered_df))
    with col2:
        total_income = filtered_df[filtered_df['transaction_type'] == 'income']['amount'].sum()
        st.metric("Total Income", f"${total_income:,.2f}")
    with col3:
        total_expenses = abs(filtered_df[filtered_df['transaction_type'] == 'expense']['amount'].sum())
        st.metric("Total Expenses", f"${total_expenses:,.2f}")
    with col4:
        net_flow = total_income - total_expenses
        st.metric("Net Flow", f"${net_flow:,.2f}")
    
    # show the actual transaction data
    st.subheader("Transaction Details")
    display_df = filtered_df.copy()
    # format amounts nicely with dollar signs
    display_df['amount'] = display_df['amount'].apply(lambda x: f"${x:,.2f}")
    display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
    
    st.dataframe(
        display_df[['date', 'description', 'amount', 'category', 'account', 'transaction_type']],
        use_container_width=True,
        height=400
    )
    
    # download button for filtered data
    if st.button("Download Filtered Data"):
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"transactions_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

def analysis_page(db):
    """advanced analytics and trend analysis"""
    st.title("Analytics Dashboard")
    
    transactions = db.load_transactions()
    accounts = db.load_accounts()
    
    if transactions.empty:
        st.warning("No transaction data available for analysis.")
        return
    
    # time period selector
    analysis_period = st.selectbox(
        "Analysis Period:",
        ["Last 30 Days", "Last 3 Months", "Last 6 Months", "All Time"]
    )
    
    # filter data based on selected period
    if analysis_period == "Last 30 Days":
        cutoff_date = datetime.now() - timedelta(days=30)
    elif analysis_period == "Last 3 Months":
        cutoff_date = datetime.now() - timedelta(days=90)
    elif analysis_period == "Last 6 Months":
        cutoff_date = datetime.now() - timedelta(days=180)
    else:
        cutoff_date = datetime.min
    
    filtered_transactions = transactions[transactions['date'] >= cutoff_date]
    
    # split into different analysis sections
    tab1, tab2, tab3 = st.tabs(["Spending Analysis", "Trends", "Net Worth"])
    
    with tab1:
        st.subheader("Spending Breakdown")
        
        # only look at expense transactions
        expenses = filtered_transactions[filtered_transactions['transaction_type'] == 'expense']
        
        if not expenses.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                # horizontal bar chart of spending by category
                category_spending = expenses.groupby('category')['amount'].sum().abs().sort_values(ascending=False)
                
                fig = px.bar(
                    x=category_spending.values,
                    y=category_spending.index,
                    orientation='h',
                    title="Spending by Category",
                    labels={'x': 'Amount ($)', 'y': 'Category'}
                )
                # dark theme styling
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_color='#fafafa'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # spending trend over time
                monthly_spending = expenses.copy()
                monthly_spending['month'] = monthly_spending['date'].dt.to_period('M')
                monthly_totals = monthly_spending.groupby('month')['amount'].sum().abs()
                
                fig = px.line(
                    x=monthly_totals.index.astype(str),
                    y=monthly_totals.values,
                    title="Monthly Spending Trend",
                    labels={'x': 'Month', 'y': 'Amount ($)'}
                )
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_color='#fafafa'
                )
                st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.subheader("Financial Trends")
        
        # monthly cash flow analysis
        monthly_data = filtered_transactions.copy()
        monthly_data['month'] = monthly_data['date'].dt.to_period('M')
        
        monthly_summary = monthly_data.groupby(['month', 'transaction_type'])['amount'].sum().unstack(fill_value=0)
        
        if 'income' in monthly_summary.columns and 'expense' in monthly_summary.columns:
            monthly_summary['net_flow'] = monthly_summary['income'] + monthly_summary['expense']
            monthly_summary['savings_rate'] = (monthly_summary['net_flow'] / monthly_summary['income'] * 100).round(2)
            
            # combined bar/line chart showing income, expenses, and net flow
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                name='Income',
                x=monthly_summary.index.astype(str),
                y=monthly_summary['income'],
                marker_color='green',
                opacity=0.7
            ))
            
            fig.add_trace(go.Bar(
                name='Expenses',
                x=monthly_summary.index.astype(str),
                y=monthly_summary['expense'],
                marker_color='red',
                opacity=0.7
            ))
            
            fig.add_trace(go.Scatter(
                name='Net Flow',
                x=monthly_summary.index.astype(str),
                y=monthly_summary['net_flow'],
                mode='lines+markers',
                line=dict(color='blue', width=3)
            ))
            
            fig.update_layout(
                title='Monthly Cash Flow Analysis',
                xaxis_title='Month',
                yaxis_title='Amount ($)',
                height=500,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='#fafafa'
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.subheader("Net Worth Breakdown")
        
        if not accounts.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                # pie chart of net worth by account type
                account_summary = accounts.groupby('account_type')['current_balance'].sum()
                
                fig = px.pie(
                    values=account_summary.values,
                    names=account_summary.index,
                    title="Net Worth by Account Type"
                )
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_color='#fafafa'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # bar chart of individual account balances
                fig = px.bar(
                    accounts,
                    x='account_name',
                    y='current_balance',
                    color='account_type',
                    title="Account Balances"
                )
                fig.update_layout(
                    xaxis_tickangle=-45,
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_color='#fafafa'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # summary numbers at the bottom
            total_assets = accounts[accounts['current_balance'] > 0]['current_balance'].sum()
            total_liabilities = abs(accounts[accounts['current_balance'] < 0]['current_balance'].sum())
            net_worth = total_assets - total_liabilities
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Assets", f"${total_assets:,.2f}")
            with col2:
                st.metric("Total Liabilities", f"${total_liabilities:,.2f}")
            with col3:
                st.metric("Net Worth", f"${net_worth:,.2f}")

if __name__ == "__main__":
    main()