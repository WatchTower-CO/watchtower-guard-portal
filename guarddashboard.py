import streamlit as st
import pandas as pd
from datetime import datetime
import sqlite3
import plotly.express as px
from zoneinfo import ZoneInfo

# ====================== LOGIN ======================
def check_login():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        st.title("🔒 Watch Tower Guard Portal Login")
        col1, col2 = st.columns([1, 2])
        with col1:
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
        
        if st.button("Login", type="primary"):
            if username == "Admin" and password == "WATCHtower123!@":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("❌ Incorrect username or password")
        st.stop()

check_login()

# ====================== STRONG LIGHT THEME ======================
st.set_page_config(page_title="Watch Tower Guard Portal", page_icon="🛡️", layout="wide")

st.markdown("""
<style>
    .stApp, .main, .block-container {
        background-color: #ffffff !important;
        color: #1e2937 !important;
    }
    .stButton>button { 
        background-color: #f97316 !important; 
        color: white !important; 
        border-radius: 6px; 
        font-weight: 600; 
    }
    h1, h2, h3 { color: #1e2937 !important; font-weight: 700; }
    
    .stTextInput input, .stSelectbox, .stDateInput input, .stTextArea textarea {
        background-color: #f8fafc !important;
        color: #1e2937 !important;
        border: 1px solid #cbd5e1 !important;
    }
    
    .event-row { 
        background-color: #f8fafc !important; 
        padding: 16px; 
        border-radius: 8px; 
        margin-bottom: 12px; 
        border: 1px solid #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)

MTZ = ZoneInfo("America/Denver")

# Sidebar
try:
    st.sidebar.image("logo.png", width=200)
except:
    try:
        st.sidebar.image("logo.jpg", width=200)
    except:
        st.sidebar.write("**🛡️ WATCH TOWER**")

st.sidebar.header("Navigation")
page = st.sidebar.radio("Go to", ["Log New Event", "Live Reports", "Performance Charts", "Guard Leaderboard", "Export & Backup"])

st.title("GUARD RESPONSE PORTAL")
st.caption("Internal • Real-Time Response Tracking • WeAreWatchTower.com")

# Database functions (same as before)
# ... (keeping the rest of your database and page code intact)

# Log New Event page with better success message
if page == "Log New Event":
    st.header("Log New Guard Response")
    with st.form("log_form"):
        col1, col2 = st.columns(2)
        with col1:
            event_date = st.date_input("Event Date", value=datetime.now(MTZ).date())
            event_time_str = st.text_input("Event Time (e.g. 12:45 or 1:30 PM)", value="12:00")
            guard = st.text_input("Dispatched Guard", value="Teddy")
        with col2:
            arrival_time_str = st.text_input("Guard Arrival Time (e.g. 12:08 or 12:08 PM)", value="12:05")
            location = st.text_input("Location", value="Auria")
            event_type = st.selectbox("Event Type", ["Alarm", "False Alarm", "Alarm Testing", "User Error", "Motion", "Door Contact", "Perimeter Breach", "Other"], index=0)
            notes = st.text_area("Notes")
        if st.form_submit_button("✅ Log Event"):
            event_dt = parse_time(str(event_date), event_time_str)
            arrival_dt = parse_time(str(event_date), arrival_time_str)
            if event_dt and arrival_dt and log_event(event_dt, guard, arrival_dt, location, event_type, notes):
                st.success("✅ Event logged successfully!")
                st.balloons()
                st.rerun()

# ... (rest of pages)

st.caption("WeAreWatchTower.com • Guard Response System")
