# 🧠 AI SQL Analyst

> **Ask questions in plain English. Get SQL queries, data, and beautiful charts — instantly.**

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://your-app.streamlit.app)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Google Gemini](https://img.shields.io/badge/AI-GPT--4o-green.svg)](https://openai.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## ✨ What It Does

AI SQL Analyst converts natural language questions into SQL queries, executes them against your database, and renders intelligent visualizations — all in one seamless interface.

```
User:  "Show me the sales trend for Q4 by product category"
   ↓
AI:    SELECT category_name, strftime('%Y-%m', order_date) AS month,
              SUM(item_total) AS revenue
       FROM sales_summary
       WHERE quarter = 'Q4'
       GROUP BY category_name, month
       ORDER BY month
   ↓
Chart: Multi-line time series, one line per category


---

## 🚀 Features

| Feature | Description |
|---|---|
| **Natural Language → SQL** | GPT-4o converts plain English to optimized SQL |
| **Auto Visualization** | Automatically picks the best chart type (line, bar, pie, scatter, heatmap) |
| **Schema Awareness** | AI reads your full schema before generating queries |
| **Multi-DB Support** | PostgreSQL, MySQL, SQLite, and any SQLAlchemy-compatible DB |
| **Safety First** | Blocks all destructive SQL (DROP, DELETE, UPDATE, etc.) |
| **Demo Database** | Built-in e-commerce dataset with 3,000 orders, 500 customers, 6 categories |
| **Export Ready** | Download any result as CSV |
| **Chat History** | Full session history with SQL, charts, and explanations |

---

## 🛠️ Tech Stack

```
Frontend:     Streamlit
AI Engine:    Google Gemini (via API)
Database ORM: SQLAlchemy
Visualization: Plotly
Data:         Pandas + NumPy
Deployment:   Streamlit Cloud
```

---

## 📦 Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/YOUR_USERNAME/ai-sql-analyst.git
cd ai-sql-analyst

python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your Gemini API key
```

`.env`:
```
OPENAI_API_KEY=sk-your-key-here
DATABASE_URL=                    # leave empty for demo DB
```

### 3. Run

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501)

---

## ☁️ Deploy to Streamlit Cloud

1. **Push to GitHub** (make sure `.env` is in `.gitignore`)

2. **Go to** [share.streamlit.io](https://share.streamlit.io) and connect your repo

3. **Set secrets** in the Streamlit Cloud dashboard:

   App → Settings → Secrets
   
   Add:
   ```toml
   GEMINI_API_KEY = "AIza-your-key-here"
   DATABASE_URL = "postgresql://..."   # optional
   

4. **Deploy** — your app will be live at `https://your-app-name.streamlit.app`

---

## 🗄️ Connecting Your Database

### PostgreSQL

postgresql://username:password@hostname:5432/database_name


### MySQL

mysql+pymysql://username:password@hostname:3306/database_name


### SQLite (local file)

sqlite:///./path/to/your/database.db


### Supabase (PostgreSQL)

postgresql://postgres:[YOUR-PASSWORD]@db.xxxx.supabase.co:5432/postgres


---

## 📊 Example Queries

Try these with the demo database:

- `Show sales trend for Q4 2023`
- `Which product categories generate the most revenue?`
- `Compare monthly order counts across all regions`
- `Who are the top 10 customers by lifetime value?`
- `Show me the distribution of order values`
- `What's the average order value by region?`
- `Which products have the lowest stock quantity?`
- `Show me completed vs refunded orders by month`

---

## 🏗️ Project Structure

```
ai-sql-analyst/
├── app.py                    # Main Streamlit application
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variable template
├── .gitignore
│
├── utils/
│   ├── ai_engine.py          # Google Gemini integration
│   ├── db_manager.py         # SQLAlchemy DB connection + query execution
│   ├── chart_builder.py      # Auto chart selection + Plotly rendering
│   └── sample_data.py        # Demo e-commerce DB generator
│
├── assets/
│   └── style.css             # Dark theme custom CSS
│
└── .streamlit/
    ├── config.toml           # Streamlit theme configuration
    └── secrets.toml.example  # Production secrets template


## 🔐 Security

- **Read-only enforcement**: All destructive SQL keywords are blocked at both the AI prompt level and the execution layer
- **API key safety**: Keys are entered in the session, never logged or stored to disk
- **Row limits**: Queries are automatically capped at 1,000 rows to prevent runaway queries
- **Input sanitization**: SQL is inspected before execution

---

## 🤝 Contributing

Pull requests welcome! For major changes, open an issue first.

```bash
# Fork → Clone → Create branch
git checkout -b feature/my-feature
# Make changes → Test → PR


## 🌟 Show Your Support

If this project helped you, give it a ⭐ on GitHub!

