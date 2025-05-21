import streamlit as st
import PyPDF2
import google.generativeai as genai
import re
import pandas as pd
import plotly.express as px
from datetime import datetime

# Category mapping for categorization of transactions
from Category import category_keywords  # Assuming Category.py is in the same directory

# 📄 Extract text from PDF
def extract_text_from_pdf(file):
    try:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            content = page.extract_text()
            if content:
                text += content + "\n"
        return text.strip()
    except Exception as e:
        st.error(f"PDF Extraction Error: {e}")
        return ""

# �🧑‍💼 Analyze financial data using Gemini
def analyze_financial_data(text, api_key):
    try:
        genai.configure(api_key=api_key)
        prompt = f"""
You are a certified financial advisor. Review the following UPI transaction data and create a detailed, professional financial analysis report.
**Guidelines:**
- Base your analysis only on the provided UPI transaction data.
- Use clear structure (headings, bullet points) and a professional tone.
- Include specific amounts from transactions in your analysis.
- Highlight key spending categories and patterns.
- Provide concrete recommendations with actionable steps.
- Avoid Disclaimers and Data Insuffcient

**Report Sections to Include**:
1. **Executive Summary**
   - Overview of financial activity.
   - Key highlights.
2. **Income vs. Expenses**
   - Total credit vs. debit amounts.
   - Net cash flow (savings or overspending).
3. **Transaction Summary**
   - Count of credit/debit transactions.
   - Notable inflows/outflows.
4. **Spending Pattern Analysis**
   - Top categories and merchants.
   - Recurring patterns (e.g., OTT, food delivery).
5. **Spending Efficiency & Potential Wastage**
   - Any inefficient or avoidable expense trends.
6. **Savings & Budget Recommendations**
   - Practical advice to reduce spending and improve financial health.
7. **Conclusion & Strategy**
   - Final insights with actionable tips.
Transaction History:
{text}
        """
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        st.error(f"Gemini Error: {e}")
        return ""

def extract_statement_period(text):
    # Try Paytm format first
    match = re.search(r"UPI Statement for\s+(\d{1,2} [A-Z]{3})'(\d{2})\s*-\s*(\d{1,2} [A-Z]{3})'(\d{2})", text)
    if match:
        start_day_month, start_year = match.group(1), match.group(2)
        end_day_month, end_year = match.group(3), match.group(4)
        try:
            start_date = datetime.strptime(f"{start_day_month} 20{start_year}", "%d %b %Y")
            end_date = datetime.strptime(f"{end_day_month} 20{end_year}", "%d %b %Y")
            return start_date, end_date
        except ValueError:
            pass
    
    # Try PhonePe format if Paytm format not found
    match = re.search(r"(\w{3} \d{2}, \d{4}) - (\w{3} \d{2}, \d{4})", text)
    if match:
        try:
            start_date = datetime.strptime(match.group(1), "%b %d, %Y")
            end_date = datetime.strptime(match.group(2), "%b %d, %Y")
            return start_date, end_date
        except ValueError:
            pass
    
    return None, None

def detect_statement_source(text):
    """Detect whether the statement is from Paytm or PhonePe"""
    if "UPI Ref No" in text and "Total Money Paid" in text:
        return "Paytm"
    elif "Transaction ID" in text and "UTR No" in text and "Transaction Statement for" in text:
        return "PhonePe"
    return "Unknown"

def parse_phonepe_data(text):
    """Parse PhonePe transaction data using line-by-line analysis"""
    transactions = []
    current_year = datetime.now().year
    
    # Clean and prepare lines
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    lines = [l for l in lines if not l.startswith("Page") and "system generated" not in l.lower()]
    
    # Enhanced patterns for matching
    date_pattern = re.compile(r"^[A-Za-z]{3} \d{1,2}, \d{4}$")  # "Mar 15, 2024"
    time_pattern = re.compile(r"\d{1,2}:\d{2} [AP]M")  # "2:30 PM"
    amount_pattern = re.compile(r"(?:INR|Rs\.?)\s*([\d,]+\.\d{2})")  # Matches both "INR 1,234.56" and "Rs. 1234.56"
    txn_id_pattern = re.compile(r"Transaction ID\s*:\s*(\w+)")
    utr_pattern = re.compile(r"UTR No\s*:\s*(\w+)")
    account_pattern = re.compile(r"(Debited from|Credited to)\s+(XX\d+|Bank Account)")
    
    i = 0
    while i < len(lines):
        if date_pattern.match(lines[i]):
            # Start of a new transaction block
            date_str = lines[i]
            i += 1
            
            # Collect all lines until next date or end
            block = []
            while i < len(lines) and not date_pattern.match(lines[i]):
                block.append(lines[i])
                i += 1
                
            try:
                # Initialize transaction fields
                time_str = ""
                description = ""
                txn_id = ""
                utr = ""
                account = ""
                txn_type = ""
                amount = 0.0
                
                # Process block lines
                for line in block:
                    # Extract time if not found yet
                    if not time_str:
                        time_match = time_pattern.search(line)
                        if time_match:
                            time_str = time_match.group()
                            
                    # Extract transaction ID
                    txn_id_match = txn_id_pattern.search(line)
                    if txn_id_match and not txn_id:
                        txn_id = txn_id_match.group(1)
                        
                    # Extract UTR
                    utr_match = utr_pattern.search(line)
                    if utr_match and not utr:
                        utr = utr_match.group(1)
                        
                    # Extract account and transaction type
                    account_match = account_pattern.search(line)
                    if account_match and not account:
                        txn_type = "Debit" if "Debited" in account_match.group(1) else "Credit"
                        account = account_match.group(2)
                        
                    # Extract amount - enhanced to handle different formats
                    amount_match = amount_pattern.search(line)
                    if amount_match:
                        amount = float(amount_match.group(1).replace(",", ""))
                        # Force negative for debits
                        if txn_type == "Debit":
                            amount = -abs(amount)
                            
                    # Extract description (first non-metadata line)
                    if (not description and not any(x in line for x in ["Transaction ID", "UTR No", "Debited from", "Credited to", "INR", "Rs."]) and 
                        not time_pattern.search(line)):
                        description = line.strip()
                
                # Enhanced datetime parsing with fallbacks
                full_datetime = None
                display_date = f"{date_str} {time_str}" if time_str else date_str
                month_year = "Unknown"
                
                try:
                    # Try parsing with current year first
                    date_obj = datetime.strptime(f"{date_str}", "%b %d, %Y")
                    if time_str:
                        try:
                            time_obj = datetime.strptime(time_str, "%I:%M %p").time()
                        except:
                            time_obj = datetime.strptime(time_str, "%H:%M").time()
                        full_datetime = datetime.combine(date_obj.date(), time_obj)
                    else:
                        full_datetime = date_obj
                    
                    display_date = full_datetime.strftime("%b %d %H:%M") if time_str else full_datetime.strftime("%b %d")
                    month_year = full_datetime.strftime("%b %Y")
                except ValueError:
                    try:
                        # Fallback to current year if year is missing
                        date_obj = datetime.strptime(f"{date_str.split(',')[0].strip()} {current_year}", "%b %d %Y")
                        if time_str:
                            time_obj = datetime.strptime(time_str, "%I:%M %p").time()
                            full_datetime = datetime.combine(date_obj.date(), time_obj)
                        else:
                            full_datetime = date_obj
                        display_date = full_datetime.strftime("%b %d %H:%M") if time_str else full_datetime.strftime("%b %d")
                        month_year = full_datetime.strftime("%b %Y")
                    except:
                        pass
                
                # Categorize transaction
                category = "Other"
                full_text = f"{description} {txn_type}".lower()
                for keyword, mapped_category in category_keywords.items():
                    if keyword in full_text:
                        category = mapped_category
                        break
                
                # Add transaction with consistent fields
                transaction = {
                    "Date": display_date,
                    "Description": description,
                    "Amount": amount,
                    "Category": category,
                    "Type": txn_type,
                    "Month_Year": month_year
                }
                
                # Add datetime fields only if we have valid dates
                if full_datetime:
                    transaction["Full_Date"] = full_datetime.strftime("%Y-%m-%d %H:%M:%S") if time_str else full_datetime.strftime("%Y-%m-%d")
                    transaction["Parsed_Date"] = full_datetime
                else:
                    transaction["Full_Date"] = None
                    transaction["Parsed_Date"] = None
                
                transactions.append(transaction)
                
            except Exception as e:
                st.warning(f"Skipping malformed transaction block: {str(e)}", icon="⚠️")
                continue
        else:
            i += 1
    
    if not transactions:
        st.error("""
        No transactions found. Possible reasons:
        1. The statement format doesn't match expected PhonePe format
        2. The PDF text extraction failed
        3. The statement is empty
        """)
    
    return transactions

def parse_paytm_data(text):
    transactions = []
    start_date, end_date = extract_statement_period(text)
    if not start_date or not end_date:
        start_date = datetime.now().replace(month=1, day=1)
        end_date = datetime.now()

    current_year = start_date.year
    previous_month = None

    # Improved pattern to capture amounts
    pattern = r"(\d{1,2} [A-Za-z]{3})\n(\d{1,2}:\d{2} [AP]M)(.*?)(?=\d{1,2} [A-Za-z]{3}\n\d{1,2}:\d{2} [AP]M|\Z)"
    matches = re.finditer(pattern, text, re.DOTALL)

    for match in matches:
        date_str = match.group(1).strip()
        time_str = match.group(2).strip()
        details = match.group(3).strip()

        try:
            day, month_abbr = date_str.split()
            month_abbr = month_abbr.upper()
            current_month = {
                'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6,
                'JUL': 7, 'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12
            }[month_abbr]

            if previous_month is not None and current_month < previous_month and previous_month == 12:
                current_year += 1
            previous_month = current_month

            try:
                time_obj = datetime.strptime(time_str, "%I:%M %p").time()
            except:
                time_obj = datetime.strptime(time_str, "%H:%M").time()

            full_datetime = datetime.combine(
                datetime(current_year, current_month, int(day)).date(),
                time_obj
            )
            display_date = full_datetime.strftime("%b %d %H:%M")
            month_year = full_datetime.strftime("%b %Y")
        except Exception as e:
            full_datetime = None
            display_date = f"{date_str} {time_str}"
            month_year = "Unknown"

        # Improved amount extraction for Paytm
        amount_match = re.search(r"([+-])\s?Rs\.?\s?(\d+(?:,\d{3})*(?:\.\d{2})?)", details)
        if amount_match:
            sign = amount_match.group(1)
            amount = float(amount_match.group(2).replace(",", ""))
            amount = -amount if sign == "-" else amount
        else:
            amount = 0.0
            
        merchant_line = details.split("\n")[0]
        merchant = re.sub(r"UPI Ref No:.*", "", merchant_line).strip()

        category = "Other"
        full_text = f"{merchant} {details}".lower()
        for keyword, mapped_category in category_keywords.items():
            if keyword in full_text:
                category = mapped_category
                break

        transactions.append({
            "Date": display_date,
            "Description": merchant,
            "Amount": amount,
            "Category": category,
            "Full_Date": full_datetime.strftime("%Y-%m-%d %H:%M:%S") if full_datetime else None,
            "Month_Year": month_year,
            "Type": "Debit" if amount < 0 else "Credit",
            "Parsed_Date": full_datetime if full_datetime else None
        })
    
    return transactions

def generate_visualizations(transactions_df):
    charts = {}
    
    if not isinstance(transactions_df, pd.DataFrame):
        transactions_df = pd.DataFrame(transactions_df)
    
    # Debug: Show raw data
    #st.write("Raw transaction data sample:", transactions_df.head(3))
    
    # Ensure Amount column exists and is numeric
    if 'Amount' not in transactions_df.columns:
        st.error("No 'Amount' column found in transaction data")
        return charts
    
    transactions_df['Amount'] = pd.to_numeric(transactions_df['Amount'], errors='coerce')
    
    # Handle date conversion - try multiple date columns if needed
    if 'Parsed_Date' in transactions_df.columns:
        transactions_df['Parsed_Date'] = pd.to_datetime(transactions_df['Parsed_Date'])
    elif 'Full_Date' in transactions_df.columns:
        transactions_df['Parsed_Date'] = pd.to_datetime(transactions_df['Full_Date'])
    elif 'Date' in transactions_df.columns:
        transactions_df['Parsed_Date'] = pd.to_datetime(transactions_df['Date'], errors='coerce')
    else:
        st.error("No valid date column found for visualization")
        return charts
    
    # Filter valid dates and amounts
    valid_dates = (transactions_df['Parsed_Date'] > pd.Timestamp('2000-01-01')) & \
                 (transactions_df['Parsed_Date'] < pd.Timestamp('2100-01-01'))
    valid_amounts = transactions_df['Amount'].notna()
    transactions_df = transactions_df[valid_dates & valid_amounts].copy()
    
    if len(transactions_df) == 0:
        st.warning("No valid transactions found for visualization")
        return charts
    
    # Create Month_Year column consistently
    transactions_df['Month_Year'] = transactions_df['Parsed_Date'].dt.strftime('%b %Y')
    
    # Sort by date for proper chronological order
    transactions_df = transactions_df.sort_values('Parsed_Date')
    
    # Debug: Show processed data
    #st.write("Processed transaction data:", transactions_df[['Date', 'Description', 'Amount', 'Category', 'Parsed_Date']].head())
    
    # Spending by Category (Pie Chart)
    try:
        debit_transactions = transactions_df[transactions_df['Amount'] < 0].copy()
        debit_transactions['Amount'] = debit_transactions['Amount'].abs()
        
        if len(debit_transactions) > 0:
            category_sum = debit_transactions.groupby('Category')['Amount'].sum().reset_index()
            fig_pie = px.pie(category_sum, 
                            values='Amount', 
                            names='Category',
                            title='Spending Distribution by Category',
                            hole=0.3)
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            charts['category_pie'] = fig_pie
        #else:
            #st.warning("No debit transactions found for category pie chart")
    except Exception as e:
        st.error(f"Error generating category pie chart: {str(e)}")
    
    # Monthly Spending Trend (Bar Chart)
    try:
        monthly_spending = debit_transactions.groupby('Month_Year')['Amount'].sum().reset_index()
        if len(monthly_spending) > 0:
            fig_bar_monthly = px.bar(monthly_spending, 
                                   x='Month_Year', 
                                   y='Amount',
                                   title='Monthly Spending Trend',
                                   labels={'Amount': 'Amount Spent (₹)', 'Month_Year': 'Month'},
                                   color='Amount',
                                   color_continuous_scale='Blues')
            fig_bar_monthly.update_xaxes(tickangle=45)
            charts['monthly_spending'] = fig_bar_monthly
        #else:
            #st.warning("No monthly spending data found")
    except Exception as e:
        st.error(f"Error generating monthly spending chart: {str(e)}")
    
    # Top Expenses (Bar Chart)
    try:
        if len(debit_transactions) > 0:
            top_expenses = debit_transactions.nlargest(10, 'Amount', keep='all')
            fig_bar = px.bar(top_expenses,
                            x='Description',
                            y='Amount',
                            title='Top 10 Expenses',
                            color='Category')
            fig_bar.update_xaxes(tickangle=45)
            charts['top_expenses'] = fig_bar
        #else:
            #st.warning("No expenses found for top expenses chart")
    except Exception as e:
        st.error(f"Error generating top expenses chart: {str(e)}")
    
    # Daily Spending Pattern (Line Chart)
    try:
        if len(debit_transactions) > 0:
            debit_transactions['Day'] = debit_transactions['Parsed_Date'].dt.day_name()
            daily_spending = debit_transactions.groupby('Day')['Amount'].sum().reset_index()
            day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            daily_spending['Day'] = pd.Categorical(daily_spending['Day'], categories=day_order, ordered=True)
            daily_spending = daily_spending.sort_values('Day')
            fig_daily = px.line(daily_spending, 
                               x='Day', 
                               y='Amount',
                               title='Daily Spending Pattern',
                               labels={'Amount': 'Amount Spent (₹)', 'Day': 'Day of Week'})
            charts['daily_spending'] = fig_daily
        #else:
            #st.warning("No data found for daily spending pattern")
    except Exception as e:
        st.error(f"Error generating daily spending chart: {str(e)}")
    
    return charts

def get_cost_control_suggestions(transactions_df):
    suggestions = {
        "Food": "Consider meal planning and cooking at home more often to reduce dining expenses.",
        "Healthcare": "Explore generic medication options and preventative care to reduce costs.",
        "Transport": "Use public transportation or carpooling when possible to save on fuel.",
        "Shopping": "Implement a 24-hour waiting period before making non-essential purchases.",
        "Entertainment": "Look for free community events and utilize library resources.",
        "Utilities": "Review subscription services and cancel unused memberships.",
        "Other": "Review these miscellaneous expenses for potential savings opportunities."
    }
    
    # Generate category-specific suggestions based on actual spending
    debit_transactions = transactions_df[transactions_df['Amount'] < 0].copy()
    debit_transactions['Amount'] = debit_transactions['Amount'].abs()
    category_spending = debit_transactions.groupby('Category')['Amount'].sum()
    
    detailed_suggestions = []
    for category, suggestion in suggestions.items():
        if category in category_spending:
            amount = category_spending[category]
            detailed_suggestions.append({
                "Category": category,
                "Amount": f"₹{amount:,.2f}",
                "Suggestion": suggestion,
                "Potential Savings": f"Potential savings: ₹{amount*0.15:,.2f} (15%)" if amount > 0 else "Review needed"
            })
    
    return pd.DataFrame(detailed_suggestions)

# 🌐 Streamlit Page Config
st.set_page_config(page_title="💸 AI Financial Analyzer", layout="wide")

# Custom CSS
st.markdown("""
<style>
    .main-title {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2E7D32;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-title {
        font-size: 1.2rem;
        color: #4CAF50;
        text-align: center;
        margin-bottom: 2rem;
    }
    .analysis-section {
        background-color: #E8F5E9;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .chart-section {
        background-color: #E3F2FD;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .suggestion-section {
        background-color: #FFF8E1;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .sidebar .sidebar-content {
        background-color: #E8F5E9;
    }
    .tab-content {
        padding: 1rem;
    }
    .detected-source {
        font-weight: bold;
        color: #1565C0;
    }
    .debug-section {
        background-color: #F5F5F5;
        padding: 1rem;
        border-radius: 5px;
        margin-bottom: 1rem;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar Configuration
st.sidebar.markdown("### 🚀 Navigation")
page = st.sidebar.radio("Select Page", ["Main Analysis", "Visualizations", "Cost Control Suggestions"])

gemini_api_key = st.sidebar.text_input("Enter your Gemini API key:", type="password")
uploaded_file = st.sidebar.file_uploader("📁 Upload your UPI Transaction PDF", type=["pdf"])

# Initialize session state
if 'transactions' not in st.session_state:
    st.session_state.transactions = None
if 'ai_response' not in st.session_state:
    st.session_state.ai_response = None
if 'visualizations' not in st.session_state:
    st.session_state.visualizations = None
if 'statement_source' not in st.session_state:
    st.session_state.statement_source = None

# Main Page Header
st.markdown('<div class="main-title">💸 Personal UPI Usage and Financial Analyzer</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">💰 Discover hidden opportunities to save and grow your wealth</div>', unsafe_allow_html=True)
# Now safely check them
if st.session_state.transactions and st.session_state.ai_response:
    st.write("Data loaded successfully!")
#else:
    #st.warning("No data loaded yet.")
# Process uploaded file
if uploaded_file and gemini_api_key:
    with st.spinner("📄 Extracting text from PDF..."):
        extracted_text = extract_text_from_pdf(uploaded_file)
    
    if extracted_text:
        with st.spinner("🔍 Detecting statement source..."):
            source = detect_statement_source(extracted_text)
            st.session_state.statement_source = source
            st.sidebar.markdown(f"**Detected Source:** <span class='detected-source'>{source}</span>", unsafe_allow_html=True)
            
            if source == "Unknown":
                st.error("❌ Unsupported statement format. Please upload Paytm or PhonePe statement.")
                st.stop()
            
        with st.spinner("🔍 Parsing transaction data..."):
            if source == "Paytm":
                transactions = parse_paytm_data(extracted_text)
            elif source == "PhonePe":
                transactions = parse_phonepe_data(extracted_text)
            else:
                st.error("❌ Unsupported statement format. Please upload Paytm or PhonePe statement.")
            
            if not transactions:
                st.error("❌ No transactions found in the statement.")
                st.stop()
                
            st.session_state.transactions = transactions
            transactions_df = pd.DataFrame(transactions)
            
            # Debug: Show parsed data
            with st.expander("Debug: View Parsed Transactions"):
                st.write(transactions_df)
            
            st.session_state.visualizations = generate_visualizations(transactions_df)
            
        # Page navigation
        if page == "Main Analysis":
            st.markdown("### 🤖 AI Financial Analysis")
            with st.spinner("🧠 Analyzing financial data..."):
                if st.session_state.ai_response is None:
                    ai_analysis = analyze_financial_data(extracted_text, gemini_api_key)
                    st.session_state.ai_response = ai_analysis
                st.markdown(f'<div class="analysis-section">{st.session_state.ai_response}</div>', unsafe_allow_html=True)
                if st.session_state.transactions and st.session_state.ai_response:
                   st.success("✅ Analysis Complete!")

            st.markdown("### 📥 Download Your Financial Report")
            
            if st.session_state.ai_response and st.session_state.visualizations:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### 📝 Analysis Report")
                    st.download_button(
                        label="Download Text Report",
                        data=st.session_state.ai_response,
                        file_name="financial_analysis_report.txt",
                        mime="text/plain"
                    )
                    
                with col2:
                    st.markdown("#### 📊 Data Export")
                    csv = pd.DataFrame(st.session_state.transactions).to_csv(index=False)
                    st.download_button(
                        label="Download Transaction Data (CSV)",
                        data=csv,
                        file_name="transaction_data.csv",
                        mime="text/csv"
                    )                
                st.markdown("---")    
                
        elif page == "Visualizations":
            st.markdown("### 📊 Transaction Visualizations")
            if st.session_state.visualizations:
                tab1, tab2, tab3, tab4 = st.tabs(["Spending Overview", "Monthly Trends", "Top Expenses", "Daily Patterns"])
                
                with tab1:
                    if 'category_pie' in st.session_state.visualizations:
                        st.plotly_chart(st.session_state.visualizations['category_pie'], use_container_width=True)
                        st.markdown("""
                        **Insights:**
                        - This pie chart shows how your spending is distributed across different categories
                        - Identify which categories consume the largest portion of your budget
                        - Hover over sections to see exact amounts and percentages
                        """)
                    else:
                        st.warning("No category data available for visualization")
                    
                with tab2:
                    if 'monthly_spending' in st.session_state.visualizations:
                        st.plotly_chart(st.session_state.visualizations['monthly_spending'], use_container_width=True)
                        st.markdown("""
                        **Insights:**
                        - Track your monthly spending patterns
                        - Identify months with unusually high or low spending
                        - Look for seasonal trends in your expenses
                        """)
                    else:
                        st.warning("No monthly spending data available for visualization")
                    
                with tab3:
                    if 'top_expenses' in st.session_state.visualizations:
                        st.plotly_chart(st.session_state.visualizations['top_expenses'], use_container_width=True)
                        st.markdown("""
                        **Insights:**
                        - These are your largest individual transactions
                        - Review if these were necessary expenses or potential areas for savings
                        - Note any recurring large expenses that could be optimized
                        """)
                    else:
                        st.warning("No top expenses data available for visualization")
                    
                with tab4:
                    if 'daily_spending' in st.session_state.visualizations:
                        st.plotly_chart(st.session_state.visualizations['daily_spending'], use_container_width=True)
                        st.markdown("""
                        **Insights:**
                        - Shows which days of the week you spend the most
                        - Weekend spending patterns often differ from weekdays
                        - Helps identify habitual spending behaviors
                        """)
                    else:
                        st.warning("No daily spending data available for visualization")
                              
        elif page == "Cost Control Suggestions":
            st.markdown("### 🧠 Cost Control Suggestions")
            if st.session_state.transactions:
                suggestions_df = get_cost_control_suggestions(pd.DataFrame(st.session_state.transactions))
                
                st.dataframe(
                    suggestions_df,
                    column_config={
                        "Category": "Category",
                        "Amount": "Amount Spent",
                        "Suggestion": "Recommendation",
                        "Potential Savings": "Estimated Savings"
                    },
                    hide_index=True,
                    use_container_width=True
                )
                
                st.markdown("---")
                st.markdown("#### 💡 Implementation Tips")
                st.markdown("""
                - **Start small**: Focus on one or two categories at a time
                - **Track progress**: Compare monthly spending after implementing changes
                - **Automate savings**: Set up automatic transfers to savings when you reduce expenses
                - **Review regularly**: Reassess your spending patterns every 3 months
                """)
                
    else:
        st.error("❌ Error extracting text from PDF. Please check the PDF format.")
else:
    if page != "Main Analysis":
        st.sidebar.warning("Please upload a PDF and provide your Gemini API key to access this page.")

