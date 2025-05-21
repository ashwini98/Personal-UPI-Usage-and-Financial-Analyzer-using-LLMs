# category_keywords mapping for transaction categorization

category_keywords = {
    # 🍽 Food & Dining
    'zomato': 'Food',
    'swiggy': 'Food',
    'restaurant': 'Food',
    'dhabha': 'Food',
    'cafe': 'Food',

    # 🚕 Travel & Transport
    'uber': 'Transport',
    'ola': 'Transport',
    'fastag': 'Transport',
    'irctc': 'Transport',
    'metro': 'Transport',

    # 🏥 Healthcare
    'hospital': 'Healthcare',
    'clinic': 'Healthcare',
    'pharmacy': 'Healthcare',
    'psg': 'Healthcare',

    # 🔌 Recharge & Utilities
    'recharge': 'Recharge',
    'electricity': 'Utilities',
    'water': 'Utilities',
    'gas': 'Utilities',

    # 💳 Financial Services
    'simpl': 'Buy Now Pay Later',
    'cred': 'Credit Card Payment',
    'loan': 'Loans',
    'emi': 'Loans',

    # 💼 Income / Salary
    'salary': 'Income',
    'credited': 'Income',
    'received': 'Income',

    # 🔄 Transfers
    'transferred': 'Transfer',
    'self': 'Transfer',
    'own account': 'Transfer',

    # 🛍 Shopping
    'amazon': 'Shopping',
    'flipkart': 'Shopping',
    'myntra': 'Shopping',

    # 🎓 Education
    'school': 'Education',
    'college': 'Education',
    'tuition': 'Education',

    # 📈 Investment & Insurance
    'insurance': 'Insurance',
    'mutual fund': 'Investment',
    'sip': 'Investment',
}

# If you prefer external (JSON) configuration, uncomment below:
# import json
# with open('category_mapping.json', 'r') as f:
#     category_keywords = json.load(f)
