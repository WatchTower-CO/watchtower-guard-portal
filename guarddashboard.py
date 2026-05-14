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
            if username == "guard" and password == "watchtower2026":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("❌ Incorrect username or password")
        st.stop()

check_login()

# ====================== BRANDING & STYLING ======================
st.set_page_config(page_title="Watch Tower Guard Portal", page_icon="🛡️", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0f172a; color: #e2e8f0; font-family: 'Helvetica', sans-serif; }
    .stButton>button { background-color: #f97316; color: white; border-radius: 6px; font-weight: 600; }
    h1, h2, h3 { color: #f8fafc; font-weight: 700; }
    .event-row { background-color: #1e2937; padding: 14px; border-radius: 8px; margin-bottom: 10px; }
    .stTextInput > div > div > input, .stSelectbox, .stDateInput, .stTimeInput { background-color: #1e2937; color: #e2e8f0; }
</style>
""", unsafe_allow_html=True)

MTZ = ZoneInfo("America/Denver")

# Sidebar Logo + Navigation
try:
    st.sidebar.image("logo.png", width=180)
except:
    try:
        st.sidebar.image("logo.jpg", width=180)
    except:
        st.sidebar.markdown("**🛡️ WATCH TOWER**")

st.sidebar.header("Navigation")
page = st.sidebar.radio("Go to", ["Log New Event", "Live Reports", "Performance Charts", "Guard Leaderboard", "Export & Backup"])

st.title("GUARD RESPONSE PORTAL")
st.caption("Internal • Real-Time Response Tracking • WeAreWatchTower.com")

# ====================== DATABASE & FUNCTIONS (unchanged) ======================
# ... [I kept all the database, parse_time, get_data, etc. the same as before]

# (The rest of your working code for the pages remains)

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
            event_type = st.selectbox("Event Type", [
                "Alarm", "False Alarm", "Alarm Testing", "User Error", 
                "Motion", "Door Contact", "Perimeter Breach", "Other"
            ], index=0)
            notes = st.text_area("Notes")
        if st.form_submit_button("✅ Log Event"):
            # (same logic as before)
            event_dt = parse_time(str(event_date), event_time_str)
            arrival_dt = parse_time(str(event_date), arrival_time_str)
            if event_dt and arrival_dt and log_event(event_dt, guard, arrival_dt, location, event_type, notes):
                st.success("✅ Event logged successfully!")
                st.rerun()

# ... (Live Reports, Performance Charts, etc. stay the same as the last full version)

st.caption("WeAreWatchTower.com • Guard Response System")
