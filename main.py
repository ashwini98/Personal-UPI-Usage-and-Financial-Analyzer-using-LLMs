import streamlit as st
import PyPDF2
import google.generativeai as genai
import re
import tempfile
import os
import pandas as pd
import plotly.express as px
from io import StringIO

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

# ✂️ Extract sections using regex
def extract_section(full_text, label):
    pattern = rf"\*\*\- {re.escape(label)}:\*\*\s*(.*?)(?=\n\*\*|\Z)"
    match = re.search(pattern, full_text, re.DOTALL)
    return match.group(1).strip() if match else "❓ Not found."

# � Analyze financial data using Gemini
def analyze_financial_data(text, api_key):
    try:
        genai.configure(api_key=api_key)
        prompt = f"""
You are a certified financial advisor. Review the following UPI transaction data and create a detailed, professional financial analysis report.
**Guidelines:**
- Base your analysis only on the provided UPI transaction data.
- Do not mention missing data or assume other expenses/income exist.
- Use clear structure (headings, bullet points) and a professional tone.
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

# 📊 Parse Paytm Transaction Data (Improved)
def parse_paytm_data(text):
    transactions = []
    
    # Improved regex pattern to match Paytm transaction blocks
    pattern = r"(\d{1,2} [A-Za-z]{3}\n\d{1,2}:\d{2} [AP]M)(.*?)(?=\d{1,2} [A-Za-z]{3}\n|\Z)"
    matches = re.finditer(pattern, text, re.DOTALL)
    
    for match in matches:
        date_time = match.group(1).replace("\n", " ")
        description = match.group(2).strip()
        
        # Extract amount - handles both formats: "Rs.100" and "Rs. 100"
        amount_match = re.search(r"([+-]) Rs?\.\s?(\d+(?:,\d{3})*(?:\.\d{2})?)", description)
        if amount_match:
            sign = amount_match.group(1)
            amount = float(amount_match.group(2).replace(",", ""))
            if sign == "-":
                amount = -amount
        else:
            amount = 0.0
        
        # Extract merchant/description
        merchant = re.sub(r"UPI Ref No:.*", "", description.split("\n")[0]).strip()
        
        # Categorize transactions
        category = None
        category_map = {
            "Food": ["dhaba", "restaurant", "food", "cafe"],
            "Healthcare": ["hospital", "pharmacy"],
            "Investments": ["groww", "investment"],
            "Transport": ["fastag", "fuel"],
            "Shopping": ["simpl", "amazon", "flipkart"],
            "Other": []
        }
        
        for cat, keywords in category_map.items():
            if any(keyword.lower() in merchant.lower() for keyword in keywords):
                category = cat
                break
        if not category:
            category = "Other"
            
        transactions.append({
            "Date": date_time,
            "Description": merchant,
            "Amount": amount,
            "Category": category
        })
    
    return transactions

# 📈 Enhanced Visualization Function
def generate_visualizations(transactions_df):
    charts = {}
    
    # Convert to DataFrame if not already
    if not isinstance(transactions_df, pd.DataFrame):
        transactions_df = pd.DataFrame(transactions_df)
    
    # Ensure proper data types
    transactions_df['Amount'] = pd.to_numeric(transactions_df['Amount'])
    
    # Improved date parsing with multiple format attempts
    date_formats = ['%d %b %I:%M %p', '%d %b %H:%M', '%d-%b-%Y', '%d/%m/%Y %H:%M']
    for fmt in date_formats:
        try:
            transactions_df['Parsed_Date'] = pd.to_datetime(transactions_df['Date'], format=fmt, errors='coerce')
            if not transactions_df['Parsed_Date'].isnull().all():
                break
        except:
            continue
    
    # 1. Spending by Category (Pie Chart)
    category_sum = transactions_df[transactions_df['Amount'] < 0].groupby('Category')['Amount'].sum().abs().reset_index()
    fig_pie = px.pie(category_sum, 
                    values='Amount', 
                    names='Category',
                    title='Spending Distribution by Category',
                    hole=0.3)
    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
    charts['category_pie'] = fig_pie
    
    # Date-based visualizations (only if valid dates)
    if 'Parsed_Date' in transactions_df and not transactions_df['Parsed_Date'].isnull().all():
        # Prepare monthly data
        monthly_data = transactions_df[transactions_df['Amount'] < 0].copy()
        monthly_data['Month'] = monthly_data['Parsed_Date'].dt.to_period('M').astype(str)
        monthly_sum = monthly_data.groupby('Month')['Amount'].sum().abs().reset_index()
        
        # 2. Monthly Spending Trend (Line Chart)
        fig_line = px.line(monthly_sum, 
                          x='Month', 
                          y='Amount',
                          title='Monthly Spending Trend',
                          markers=True)
        fig_line.update_layout(yaxis_title='Amount (₹)')
        charts['monthly_trend'] = fig_line
        
        # 2a. Monthly Spending Trend (Bar Chart)
        fig_bar = px.bar(monthly_sum,
                        x='Month',
                        y='Amount',
                        title='Monthly Spending Trend (Bar Chart)',
                        text='Amount',
                        labels={'Amount': 'Amount (₹)'})
        fig_bar.update_traces(texttemplate='₹%{text:.2f}', textposition='outside')
        fig_bar.update_layout(xaxis_title='Month', yaxis_title='Amount (₹)')
        charts['monthly_trend_bar'] = fig_bar
        
        # 4. Category-wise Monthly Breakdown (Heatmap)
        heatmap_data = transactions_df[transactions_df['Amount'] < 0].copy()
        heatmap_data['Month'] = heatmap_data['Parsed_Date'].dt.to_period('M').astype(str)
        heatmap_data['Amount'] = heatmap_data['Amount'].abs()
        
        category_month = heatmap_data.groupby(['Category', 'Month'])['Amount'].sum().unstack().fillna(0)
        
        fig_heatmap = px.imshow(category_month,
                              labels=dict(x="Month", y="Category", color="Amount"),
                              title='Monthly Spending by Category',
                              aspect="auto")
        fig_heatmap.update_xaxes(side="top")
        charts['category_heatmap'] = fig_heatmap
    
    # 3. Top Expenses (Bar Chart) - Doesn't require dates
    top_expenses = transactions_df[transactions_df['Amount'] < 0].nlargest(10, 'Amount', keep='all').copy()
    top_expenses['Amount'] = top_expenses['Amount'].abs()
    top_expenses['Description'] = top_expenses['Description'].str.wrap(30).apply(lambda x: x.replace('\n', '<br>'))
    
    fig_top = px.bar(top_expenses,
                    x='Description',
                    y='Amount',
                    title='Top 10 Expenses',
                    text='Amount',
                    hover_data=['Category'])
    fig_top.update_traces(texttemplate='₹%{text:.2f}', textposition='outside')
    fig_top.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
    charts['top_expenses'] = fig_top
    
    return charts

# 📊 Generate Category Breakdown and Suggestions
def generate_category_breakdown_and_suggestions(transactions):
    df = pd.DataFrame(transactions)
    
    # Calculate category breakdown
    category_breakdown = df.groupby("Category").agg({
        "Amount": ["sum", "count"],
        "Description": lambda x: ", ".join(x.unique())
    }).reset_index()
    
    category_breakdown.columns = ["Category", "Total Amount", "Transaction Count", "Merchants"]
    
    # Generate suggestions
    cost_control_suggestions = {
        "Food": "Consider reducing eating out expenses. Meal prepping can save money.",
        "Healthcare": "Review if all medical expenses are essential. Check for insurance coverage.",
        "Investments": "Continue regular investments but review portfolio periodically.",
        "Transport": "Explore carpooling or public transport to reduce FASTag/fuel costs.",
        "Shopping": "Set a monthly shopping budget and stick to essentials.",
        "Other": "Review miscellaneous expenses for potential savings."
    }
    
    return category_breakdown, cost_control_suggestions

# 🌐 Streamlit Page Config
st.set_page_config(page_title="💸 AI Financial Analyzer", layout="wide")

# Sidebar Configuration
st.sidebar.markdown("### 🚀 Navigation")
page = st.sidebar.radio("Select Page", ["Main Analysis", "Visualizations"])

gemini_api_key = st.sidebar.text_input("Enter your Gemini API key:", type="password")
uploaded_file = st.sidebar.file_uploader(":file_folder: **Upload your UPI Transaction PDF(Paytm)**", type=["pdf"])

# Main Page Header
st.markdown("""
    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; padding-top: 20px;">
        <h1 style="font-size: 3em; text-align: center;">💸 Personal UPI Usage and Financial Analyzer</h1>
        <p style="font-size: 1.5em; text-align: center;">💰 Discover hidden opportunities to save and grow your wealth</p>
    </div>
""", unsafe_allow_html=True)

# Initialize session state
if 'transactions' not in st.session_state:
    st.session_state.transactions = None
if 'ai_response' not in st.session_state:
    st.session_state.ai_response = None

# Process uploaded file
if uploaded_file and gemini_api_key:
    with st.spinner("📄 Extracting text from PDF..."):
        extracted_text = extract_text_from_pdf(uploaded_file)
    
    if extracted_text:
        paytm_transactions = parse_paytm_data(extracted_text)
        
        if paytm_transactions:
            st.session_state.transactions = paytm_transactions
            
            transactions_text = "\n".join([
                f"{txn['Date']} | {txn['Description']} | {txn['Amount']} | {txn['Category']}"
                for txn in paytm_transactions
            ])
            
            with st.spinner("🔎 Analyzing with Gemini AI..."):
                st.session_state.ai_response = analyze_financial_data(transactions_text, gemini_api_key)

# Page Navigation
if page == "Main Analysis":
    if st.session_state.transactions and st.session_state.ai_response:
        st.success("✅ Analysis Complete!")
        
        category_breakdown, cost_suggestions = generate_category_breakdown_and_suggestions(st.session_state.transactions)
        
        st.markdown("### 📊 Category-wise Breakdown")
        st.dataframe(category_breakdown)
        
        st.markdown("### 🧠 Cost Control Suggestions")
        for category in category_breakdown["Category"]:
            if category in cost_suggestions:
                st.markdown(f"**{category}:** {cost_suggestions[category]}")
        
        with st.expander("📜 View Full AI Analysis Report", expanded=True):
            st.markdown(st.session_state.ai_response)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
            tmp.write(st.session_state.ai_response.encode("utf-8"))
            report_path = tmp.name
        
        with open(report_path, "rb") as f:
            st.download_button(
                "📥 Download AI Report",
                f,
                file_name="Financial_Analysis_Report.txt",
                mime="text/plain"
            )
        
        try: os.unlink(report_path)
        except: pass

elif page == "Visualizations":
    if st.session_state.transactions:
        st.markdown("## 📈 Spending Patterns Visualization")
        
        try:
            charts = generate_visualizations(pd.DataFrame(st.session_state.transactions))
            
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "Category Distribution", 
                "Monthly Trends", 
                "Top Expenses", 
                "Category Heatmap",
                "Monthly Bar Chart"
            ])
            
            with tab1:
                st.plotly_chart(charts['category_pie'], use_container_width=True)
            
            with tab2:
                if 'monthly_trend' in charts:
                    st.plotly_chart(charts['monthly_trend'], use_container_width=True)
                else:
                    st.warning("""
                    **Insufficient date data for monthly trends**  
                    Could not reliably parse dates from your transactions.  
                    Ensure your statement includes complete date information.
                    """)
            
            with tab3:
                st.plotly_chart(charts['top_expenses'], use_container_width=True)
            
            with tab4:
                if 'category_heatmap' in charts:
                    st.plotly_chart(charts['category_heatmap'], use_container_width=True)
                else:
                    st.warning("Insufficient date data for category heatmap")
            
            with tab5:
                if 'monthly_trend_bar' in charts:
                    st.plotly_chart(charts['monthly_trend_bar'], use_container_width=True)
                else:
                    st.warning("Insufficient date data for monthly bar chart")
        
        except Exception as e:
            st.error(f"Visualization Error: {str(e)}")
    else:
        st.warning("Please upload a PDF file and enter your API key to view visualizations")

if not uploaded_file or not gemini_api_key:
    st.sidebar.warning("⚠️ Please upload a PDF and enter your Gemini API key.")

