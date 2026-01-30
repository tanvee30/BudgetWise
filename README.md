
# 💰 BudgetWise - Intelligent Budget Recommendation Engine

An AI-powered personal finance platform that generates realistic, personalized budget recommendations by analyzing historical transaction data and spending patterns.

![BudgetWise Dashboard](https://img.shields.io/badge/Django-4.2-green) ![Python](https://img.shields.io/badge/Python-3.13-blue) ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13+-blue)


 📋 Table of Contents

- [Overview]
- [Key Features]
- [Tech Stack]
- [Installation & Setup]
- [Usage Guide]
- [API Documentation]
- [Project Structure]
- [Budget Calculation Logic]
- [Enhancements Beyond Requirements]
- [Testing]
- [Future Improvements]


🎯 Overview

BudgetWise solves a critical problem in personal finance: budget adherence. Most budgeting tools fail because they:
- Use unrealistic, one-size-fits-all recommendations
- Require manual configuration
- Disconnect from actual spending behavior

Our Solution:
BudgetWise automatically analyzes your spending patterns over the last 1-3 months and generates intelligent, personalized budget recommendations with clear explanations for every decision.

✨ Key Features

Core Features (As Per Requirements)

1.Intelligent Budget Recommendations🧠
- Analyzes 1-3 months of historical transaction data
- Calculates average spending per category
- Identifies high-volatility and irregular spending patterns
- Generates realistic monthly and weekly budgets
- NO fixed rules(e.g., "save 20% of income")
- Savings recommendations based on actual behavior

2.Expense Classification📊
Automatically categorizes expenses into:
- Fixed Expenses: Rent, EMI, subscriptions (predictable, recurring)
- Variable Essentials: Food, transport (necessary but varies)
- Discretionary: Entertainment, shopping (optional spending)

3.Explainability (Critical Feature) 💡
Every recommendation includes human-readable explanations:
- "Food budget is ₹6,500 based on your 3-month average of ₹6,200 with a 10% buffer for volatility"
- "Entertainment spending flagged as high-risk due to 35% increase last month"
- "Savings limited this month due to higher fixed commitments"

4.Financial Health Indicators 📈
- Income Stability Score (0-100): How consistent is income
- Expense Volatility Score (0-100): Spending predictability
- Savings Confidence Indicator (0-100): Likelihood of meeting savings goals

5.Weekly Budget Breakdown 📅
- Breaks monthly budgets into manageable weekly chunks
- Helps track progress throughout the month
- Includes weekly spending and savings targets

6.Edge Case Handling ⚠️
Thoughtfully handles:
- Users with limited transaction history
- One-time large/anomalous expenses (hospital bills, electronics)
- Inconsistent spending patterns
- Sudden income increases or drops


🌟 Enhanced Features (Beyond Requirements)

7. Interactive Data Visualizations 📊
- Spending by Category**: Doughnut chart showing expense distribution
- Monthly Spending Trend**: Line chart tracking spending over 6 months
- Budget vs Actual Comparison**: Side-by-side bar chart
- Built with Chart.js for smooth, interactive experience

8.Budget Adherence Score 🎯
- Real-time score (0-100) showing how well you're following your budget
- Color-coded visual gauge (green/yellow/red)
- Category-specific insights and warnings
- Monthly spending summary with remaining budget

9.Smart Transaction Management** 💳
- Search: Find transactions by merchant name
- Filter by Category: View specific spending categories
- Filter by Month: Analyze spending for any month
- Transaction Counter: Shows filtered results count
- Add Transaction Modal: Beautiful centered popup for adding expenses

10.Export to PDF 📄
- One-click budget report export
- Professional formatting with headers
- Includes all category breakdowns and recommendations
- Perfect for sharing or record-keeping

11.Custom Modal System ✨
- Beautiful, centered confirmation dialogs
- Success modals with animated checkmarks
- Error modals with clear messaging
- No more ugly browser alerts!

12.Responsive Design📱
- Mobile-friendly interface
- Works seamlessly on desktop, tablet, and phone
- Clean, modern UI with Inter font family



🛠️ Tech Stack

Backend
- Django 4.2 - Web framework
- Django REST Framework - API development
- PostgreSQL 13+ - Database
- Python 3.13 - Programming language

Frontend
- HTML5/CSS3 - Structure and styling
- JavaScript (Vanilla)** - Client-side logic
- Chart.js - Data visualizations
- HTML2PDF.js - PDF export functionality

Development Tools
- Git - Version control
- VS Code- Code editor
- pgAdmin - Database management

---

🚀 Installation & Setup

Prerequisites
- Python 3.10 or higher
- PostgreSQL 13 or higher
- Git

Step 1: Clone Repository
```bash
git clone https://github.com/tanvee30/BudgetWise
cd BudgetWise
```

Step 2: Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

Step 4: Configure Database

Create PostgreSQL Database:
sql
-- Using psql
psql -U postgres
CREATE DATABASE budgetwise_db;
\q


Update `budgetwise_project/settings.py`:

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'budgetwise_db',
        'USER': 'postgres',
        'PASSWORD': 'postgres',  
        'HOST': 'localhost',
        'PORT': '5432',
    }
}


Step 5: Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

Step 6: Create Superuser
```bash
python manage.py createsuperuser
```

Step 7: Load Sample Data (Optional)
```bash
python manage.py seed_data --months 3
```

This creates:
- Test user (username: `testuser`, password: `testpass123`)
- ~250-300 realistic transactions over 3 months
- Financial profile with income and stability scores

Step 8: Run Server
```bash
python manage.py runserver
```

Visit: http://127.0.0.1:8000/



📖 Usage Guide

1.Login
- Go to http://127.0.0.1:8000/login/
- Use test credentials: `testuser` / `testpass123`
- Or create your own account

2.View Dashboard
- See financial overview with 4 key metrics
- View interactive charts:
  - Spending by category
  - Monthly spending trend
  - Budget vs actual comparison
- Check budget adherence score

3.Manage Transactions
- Click "Transactions"in navbar
- Add new transaction: Click "+ Add Transaction" button
- Search: Type merchant name in search box
- Filter: Select category or month
- View details: All transactions in sortable table

4.Generate Budget
- Click "Budget" in navbar
- Click "Generate New Budget"button
- System analyzes your spending patterns
- View personalized recommendations with explanations
- See category-wise budgets with risk levels
- Check weekly breakdown

5.Export Budget
- On Budget page, click "📄 Export PDF"
- Professional PDF report downloads automatically
- Includes all recommendations and categories



🔌 API Documentation

Base URL

http://127.0.0.1:8000/api/


Authentication
Session-based authentication (login required for all endpoints)

Endpoints

1.User Financial Profile

GET /api/profile/
[
  {
    "id": 1,
    "username": "testuser",
    "monthly_income": "50000.00",
    "income_stability_score": 85.0,
    "expense_volatility_score": 36.4,
    "savings_confidence_indicator": 53.1
  }
]

PUT /api/profile/{id}/
json
Request:
{
    "monthly_income": "60000.00"
}


2.Transactions

GET  /api/transactions/
- Returns paginated list of all transactions

POST  /api/transactions/
json
Request:
{
    "amount": "500.50",
    "date": "2026-01-28",
    "merchant_name": "Swiggy",
    "category": "food",
    "expense_type": "discretionary",
    "transaction_source": "upi"
}


GET /api/transactions/recent/
- Returns transactions from last 30 days

GET  /api/transactions/by_category/
- Returns spending summary grouped by category



3.Budget Recommendations

POST /api/budgets/generate/
json
Request (optional):
{
    "target_month": "2026-03-01"
}

Response:
{
    "message": "Budget generated successfully",
    "budget": {
        "month": "2026-03-01",
        "recommended_savings": "13726.32",
        "savings_reason": "Excellent financial discipline!...",
        "total_recommended_budget": "22547.36",
        "category_budgets": [...],
        "weekly_budgets": [...]
    }
}

GET  /api/budgets/latest/
- Returns most recent budget recommendation

GET /api/budgets/{id}/compare/
- Compares budgeted vs actual spending

GET /api/budgets/adherence/
- Returns budget adherence score and insights



📁 Project Structure

BudgetWise/
├── budgetwise_project/          # Django project settings
│   ├── settings.py              # Configuration
│   ├── urls.py                  # Main URL routing
│   └── wsgi.py                  # WSGI config
├── finance/                     # Main application
│   ├── models.py                # Database models
│   ├── views.py                 # API views
│   ├── serializers.py           # DRF serializers
│   ├── services.py              # Budget calculation logic
│   ├── admin.py                 # Admin panel config
│   ├── urls.py                  # App URL routing
│   └── management/
│       └── commands/
│           ├── seed_data.py     # Sample data generator
│           └── test_budget.py   # Budget testing command
├── templates/                   # HTML templates
│   ├── base.html                # Base template
│   ├── dashboard.html           # Dashboard page
│   ├── transactions.html        # Transactions page
│   ├── budget.html              # Budget page
│   └── login.html               # Login page
├── static/                      # Static files
│   ├── css/
│   │   └── style.css            # All styles
│   └── js/
│       ├── dashboard.js         # Dashboard logic
│       ├── transactions.js      # Transaction management
│       └── budget.js            # Budget display logic
├── manage.py                    # Django management script
├── requirements.txt             # Python dependencies
└── README.md                    # This file


 🧮 Budget Calculation Logic

Core Algorithm
python
def generate_budget_recommendation():
    1. Analyze last 1-3 months of transactions
    2. Calculate average spending per category
    3. Calculate spending volatility (std dev / mean)
    4. Classify expenses (fixed/variable/discretionary)
    5. Apply intelligent buffering:
       - Fixed: 5% buffer
       - Variable (low volatility): 10-15% buffer
       - Variable (high volatility): 20% buffer
       - Discretionary (high volatility): Recommend reduction
    6. Calculate realistic savings:
       - NOT a fixed percentage
       - Based on: income - expenses - volatility buffer
       - Adjusted for spending stability
    7. Generate explanations for each decision
    8. Create weekly breakdowns


Example Calculation

Input:
- Monthly Income: ₹50,000
- Food spending last 3 months: ₹6,000, ₹6,200, ₹6,400
- Volatility: Low (std dev: ₹200)

Output:
- Average: ₹6,200
- Volatility Score: 3.2% (low)
- Recommended Budget: ₹6,820 (₹6,200 + 10% buffer)
- Reason: "Your food spending is stable at ₹6,200/month. Added 10% buffer for minor fluctuations."


🌟 Enhancements Beyond Requirements

What Was NOT Required But We Added:



1.Interactive Charts     :Visual data is easier to understand than numbers 
2.Budget Adherence Score :Gamifies budgeting, encourages good behavior 
3.Search & Filter        :Essential for managing many transactions 
4.Custom Modals          :Professional UX, better than browser alerts 
5.PDF Export             :Enables sharing and record-keeping 
6.Weekly Breakdown       :Makes monthly budgets more manageable 
7.Responsive Design      :Mobile users are majority of audience 
8.Real-time Insights     :Proactive warnings prevent overspending 

Technical Innovations:

1. No Fixed Rules: Unlike competitors, we never use "save 20% of income" type rules
2. Anomaly Detection: Automatically identifies one-time expenses
3. Volatility Analysis: Uses statistical methods (std dev) for risk assessment
4. Context-Aware Explanations**: Recommendations adapt to user's situation
5. Progressive Enhancement: Core features work without JavaScript



✅ Testing

Manual Testing Checklist

- [ ] User can login/logout
- [ ] Dashboard loads with correct stats
- [ ] Charts render properly
- [ ] Transactions can be added
- [ ] Search and filters work
- [ ] Budget generation succeeds
- [ ] Budget explanations are clear
- [ ] PDF export works
- [ ] Adherence score displays
- [ ] Responsive on mobile

Test Budget Generation
```bash
python manage.py test_budget
```


🔮 Future Improvements

1. Machine Learning: Predict future spending patterns
2. Multi-currency Support: For international users
3. Bank Integration: Automatic transaction import
4. Goal Tracking: Save for specific targets
5. Notifications using Celery & Celery Beat: Email/SMS alerts for overspending
6. Collaborative Budgets: Family/household budgeting
7. Investment Recommendations: Based on savings capacity
8. Receipt Scanning: OCR for automatic entry



👨‍💻 Developer

Tanvee Saxena
- GitHub:https://github.com/tanvee30
- Email: tanveesaxena30@gmail.com
- LinkedIn:https://www.linkedin.com/in/tanvee-saxena-74a001282/



📄 License

This project was created as part of a Django Developer assignment.


🙏 Acknowledgments

- Assignment by Team Necessive 
- Chart.js for beautiful visualizations
- Django & DRF communities for excellent documentation
- PostgreSQL for robust data storage



📧 Support

For questions or issues:
1. Open an issue on GitHub
2. Email: tanveesxena30@gmail.com
3. Review the documentation above

---

Made with ❤️ and Django