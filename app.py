import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sqlalchemy
from sqlalchemy import create_engine, text, inspect
from google import genai
import os
import json
import re
from datetime import datetime, timedelta
import time
from utils.db_manager import DBManager
from utils.ai_engine import AIEngine
from utils.chart_builder import ChartBuilder
from utils.sample_data import initialize_sample_db

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI SQL Analyst",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Load Custom CSS ───────────────────────────────────────────────────────────
with open("assets/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ── Session State Init ────────────────────────────────────────────────────────
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "db_engine" not in st.session_state:
    st.session_state.db_engine = None
if "db_schema" not in st.session_state:
    st.session_state.db_schema = None
if "query_results" not in st.session_state:
    st.session_state.query_results = []
if "gemini_key_set" not in st.session_state:
    st.session_state.gemini_key_set = False

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-header">
        <div class="logo-icon">🧠</div>
        <div>
            <div class="logo-title">AI SQL Analyst</div>
            <div class="logo-sub">Natural Language → Insights</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ── API Key ──────────────────────────────────────────────────────────────
    st.markdown("### 🔑 Gemini Configuration")
    api_key_input = st.text_input(
        "API Key",
        type="password",
        placeholder="AIza...",
        value=os.getenv("GEMINI_API_KEY", ""),
        help="Free key from aistudio.google.com. Never stored."
    )
    model_choice = st.selectbox(
        "Model",
        ["gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-1.5-flash"],
        index=0
    )
    if api_key_input:
        st.session_state.gemini_api_key = api_key_input
        st.session_state.gemini_model = model_choice
        st.session_state.gemini_key_set = True
        st.success("✅ API key configured")

    st.markdown("---")

    # ── Database Connection ──────────────────────────────────────────────────
    st.markdown("### 🗄️ Database Connection")
    db_mode = st.radio(
        "Source",
        ["🎲 Demo Database", "🔌 Custom Connection"],
        index=0
    )

    if db_mode == "🎲 Demo Database":
        if st.button("🚀 Load Demo Data", use_container_width=True):
            with st.spinner("Loading sample e-commerce database..."):
                engine = initialize_sample_db()
                st.session_state.db_engine = engine
                db_mgr = DBManager(engine)
                st.session_state.db_schema = db_mgr.get_schema_info()
                st.success("✅ Demo DB loaded!")
                st.rerun()
    else:
        db_url = st.text_input(
            "Connection String",
            placeholder="postgresql://user:pass@host:5432/db",
            help="SQLAlchemy connection string"
        )
        if st.button("🔌 Connect", use_container_width=True) and db_url:
            try:
                engine = create_engine(db_url)
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                st.session_state.db_engine = engine
                db_mgr = DBManager(engine)
                st.session_state.db_schema = db_mgr.get_schema_info()
                st.success("✅ Connected!")
                st.rerun()
            except Exception as e:
                st.error(f"Connection failed: {e}")

    # ── Schema Preview ───────────────────────────────────────────────────────
    if st.session_state.db_schema:
        st.markdown("---")
        st.markdown("### 📋 Schema")
        for table, cols in st.session_state.db_schema.items():
            with st.expander(f"📊 {table}", expanded=False):
                for col in cols:
                    st.markdown(f"<span class='col-badge'>{col['name']}</span> <span class='col-type'>{col['type']}</span>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 💡 Example Queries")
    example_queries = [
        "Show sales trend for Q4 2023",
        "Which products have the highest revenue?",
        "Compare monthly sales by category",
        "Show top 10 customers by order value",
        "What's the average order value by region?",
        "Show me orders with above average value",
    ]
    for q in example_queries:
        if st.button(q, use_container_width=True, key=f"ex_{q[:20]}"):
            st.session_state.pending_query = q
            st.rerun()

# ── Main Content ──────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>AI SQL Analyst <span class="beta-badge">BETA</span></h1>
    <p>Ask questions in plain English — get SQL queries, data, and beautiful charts instantly.</p>
</div>
""", unsafe_allow_html=True)

# ── Status Bar ───────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
with col1:
    db_status = "🟢 Connected" if st.session_state.db_engine else "🔴 No Database"
    st.markdown(f"<div class='stat-card'><div class='stat-label'>Database</div><div class='stat-value'>{db_status}</div></div>", unsafe_allow_html=True)
with col2:
    ai_status = "🟢 Ready" if st.session_state.gemini_key_set else "🔴 No API Key"
    st.markdown(f"<div class='stat-card'><div class='stat-label'>AI Engine</div><div class='stat-value'>{ai_status}</div></div>", unsafe_allow_html=True)
with col3:
    n_tables = len(st.session_state.db_schema) if st.session_state.db_schema else 0
    st.markdown(f"<div class='stat-card'><div class='stat-label'>Tables</div><div class='stat-value'>{n_tables} available</div></div>", unsafe_allow_html=True)
with col4:
    n_queries = len(st.session_state.chat_history)
    st.markdown(f"<div class='stat-card'><div class='stat-label'>Queries Run</div><div class='stat-value'>{n_queries} this session</div></div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Chat Interface ────────────────────────────────────────────────────────────
chat_container = st.container()

# Render history
with chat_container:
    for i, entry in enumerate(st.session_state.chat_history):
        # User bubble
        st.markdown(f"""
        <div class="chat-user">
            <div class="chat-avatar user-avatar">👤</div>
            <div class="chat-bubble user-bubble">{entry['question']}</div>
        </div>
        """, unsafe_allow_html=True)

        # AI response
        st.markdown(f"""
        <div class="chat-ai-header">
            <div class="chat-avatar ai-avatar">🧠</div>
            <div class="chat-meta">AI Analyst · {entry.get('timestamp','')}</div>
        </div>
        """, unsafe_allow_html=True)

        if entry.get("error"):
            st.error(entry["error"])
        else:
            # SQL Display
            with st.expander("📝 Generated SQL", expanded=False):
                st.code(entry.get("sql", ""), language="sql")

            # Explanation
            if entry.get("explanation"):
                st.markdown(f"<div class='ai-explanation'>{entry['explanation']}</div>", unsafe_allow_html=True)

            # Chart
            if entry.get("chart"):
                st.plotly_chart(entry["chart"], use_container_width=True, key=f"chart_{i}")

            # DataFrame
            if entry.get("dataframe") is not None:
                df = entry["dataframe"]
                st.markdown(f"<div class='result-meta'>📊 {len(df)} rows · {len(df.columns)} columns</div>", unsafe_allow_html=True)
                st.dataframe(df, use_container_width=True, height=min(300, 50 + len(df) * 35))

                col_dl1, col_dl2 = st.columns([1, 5])
                with col_dl1:
                    csv = df.to_csv(index=False)
                    st.download_button(
                        "⬇️ CSV",
                        csv,
                        file_name=f"query_{i+1}.csv",
                        mime="text/csv",
                        key=f"dl_{i}"
                    )

        st.markdown("<hr class='chat-divider'>", unsafe_allow_html=True)

# ── Query Input ───────────────────────────────────────────────────────────────
st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)

pending = st.session_state.pop("pending_query", None)

with st.form(key="query_form", clear_on_submit=True):
    cols = st.columns([8, 1])
    with cols[0]:
        user_input = st.text_input(
            "Ask anything about your data",
            value=pending or "",
            placeholder="e.g. Show me the top 5 products by revenue last quarter...",
            label_visibility="collapsed"
        )
    with cols[1]:
        submitted = st.form_submit_button("▶ Run", use_container_width=True)

# ── Process Query ─────────────────────────────────────────────────────────────
if submitted and user_input:
    if not st.session_state.gemini_key_set:
        st.error("⚠️ Please enter your Gemini API key in the sidebar. Get one free at aistudio.google.com")
    elif not st.session_state.db_engine:
        st.error("⚠️ Please connect to a database first (or load the Demo DB).")
    else:
        with st.spinner("🧠 Thinking..."):
            try:
                ai = AIEngine(
                    api_key=st.session_state.gemini_api_key,
                    model=st.session_state.gemini_model,
                    schema=st.session_state.db_schema
                )
                result = ai.process_query(user_input)
                sql = result["sql"]

                db_mgr = DBManager(st.session_state.db_engine)
                df = db_mgr.execute_query(sql)

                chart_builder = ChartBuilder()
                fig = chart_builder.auto_chart(df, user_input, result.get("chart_type", "auto"))

                st.session_state.chat_history.append({
                    "question": user_input,
                    "sql": sql,
                    "explanation": result.get("explanation", ""),
                    "dataframe": df,
                    "chart": fig,
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                })

            except Exception as e:
                st.session_state.chat_history.append({
                    "question": user_input,
                    "sql": "",
                    "error": f"Error: {str(e)}",
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                })

        st.rerun()

# ── Clear History ─────────────────────────────────────────────────────────────
if st.session_state.chat_history:
    if st.button("🗑️ Clear History", key="clear"):
        st.session_state.chat_history = []
        st.rerun()

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="footer">
    Built with Streamlit · Google Gemini · SQLAlchemy · Plotly
</div>
""", unsafe_allow_html=True)


