
# 💸 Personal UPI Usage and Financial Analyzer using LLMs

An AI-powered FinTech application that processes UPI transaction PDFs (Paytm), extracts transaction details, analyzes financial behavior, and provides personalized recommendations using Google Gemini 1.5 Flash.

---

## 🔍 Problem Statement

Develop an AI-driven personal finance assistant that:
- Extracts transaction data from various UPI PDF formats.
- Structures and analyzes the data to detect spending behavior.
- Uses LLMs to generate financial insights and suggestions.
- Presents results through an interactive dashboard or downloadable report.

---

## 💼 Domain

**FinTech / Personal Finance Automation**

---

## 🚀 Business Use Cases

- **Personal Finance Management**: Understand income vs. spending.
- **Spending Habit Detection**: Identify recurring patterns, top merchants, and inefficient expenses.
- **Budgeting Assistant**: Generate AI-based savings strategies.
- **Multi-App Integration**: Unify UPI data from multiple sources.Here, only Paytm is Given 

---

## 🛠️ Features

- 📄 PDF Upload (Paytm supported)
- 🧠 LLM-based Report Generation using Gemini 1.5 Flash
- 📊 Visualizations: Pie charts, bar graphs, heatmaps, top expenses
- 📥 Downloadable AI Financial Report
- ✅ Clean and interactive UI built with Streamlit
- ☁️ Easily deployable on Streamlit Community Cloud (free)

---

## 🧠 Skills You’ll Learn

- ✅ PDF Data Extraction and Parsing
- ✅ Data Cleaning and Structuring with Pandas
- ✅ Google Gemini LLM Integration
- ✅ Financial Data Analysis and Recommendation Logic
- ✅ Streamlit App Development & Deployment

---

## 📦 Tech Stack

| Component        | Technology                   |
|------------------|------------------------------|
| Language         | Python 3.9+                  |
| LLM              | Google Gemini 1.5 Flash      |
| UI Framework     | Streamlit                    |
| PDF Parsing      | PyPDF2                       |
| Visualization    | Plotly                       |
| Deployment       | Streamlit                    |

---

## 📂 Project Structure

```
📁 upi-finance-analyzer/
│
├── main.py # Main Streamlit application
├── requirements.txt # Python dependencies
├── README.md # Project documentation
├── sample_statements/ # Example PDFs (not included in repo)
└── .streamlit/
└── secrets.toml # API keys (Gemini, etc.) for local/deployment use

```

---

## 🧪 How to Run Locally

1. **Clone the repository**:
   ```bash
   git clone https://github.com/ashwini98/upi-financial-analyzer.git
   cd upi-financial-analyzer
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the app**:
   ```bash
   streamlit run app.py
   ```

5. **Enter your Gemini API Key** when prompted in the sidebar.

---

## 🚀 Streamlit Deployment (Free)

You can easily deploy this app using **Streamlit Community Cloud**:

### 1. Push to GitHub

Ensure your project contains:

- `main.py` (main app)
- `requirements.txt`
- `README.md`

### 2. Deploy on Streamlit Cloud

- Visit: [https://streamlit.io/cloud](https://streamlit.io/cloud)
- Click **"Sign in with GitHub"**
- Click **"New app"**
- Select your repo, branch, and `app.py` as the file
- Click **"Deploy"**

> 🔐 Don't forget to **add your Gemini API key securely** using Streamlit's [Secrets Manager](https://docs.streamlit.io/streamlit-community-cloud/get-started/deploy-an-app/secrets-management).

```toml
# .streamlit/secrets.toml
GEMINI_API_KEY = "your_key_here"
```

Access it in your code like this:

```python
import streamlit as st
api_key = st.secrets["GEMINI_API_KEY"]
```

---

## 🎥 Demo

Video walkthrough coming soon!  
📺 _["D:\personal_upi_finance_analyzer\AI Powered Financial Analyzer.mp4"]_

---

## 🤝 Contributors

We welcome contributions! To contribute:

1. Fork this repo
2. Create a feature branch: `git checkout -b new-feature`
3. Commit changes: `git commit -m 'Add new feature'`
4. Push to branch: `git push origin new-feature`
5. Open a Pull Request (PR)

---

## ⭐ Star This Project

If you found this project helpful, please give it a ⭐ on GitHub. It helps others discover it!

