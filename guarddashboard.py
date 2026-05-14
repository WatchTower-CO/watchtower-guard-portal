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

# ====================== BRANDING ======================
st.set_page_config(page_title="Watch Tower Guard Portal", page_icon="🛡️", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #ffffff; color: #1e2937; font-family: 'Helvetica', Arial, sans-serif; }
    .stButton>button { background-color: #f97316; color: white; border-radius: 6px; font-weight: 600; padding: 10px 24px; }
    h1 { color: #1e2937; font-weight: 700; letter-spacing: -0.5px; }
    h2, h3 { color: #1e2937; }
    .stTextInput input, .stSelectbox, .stDateInput input {
        background-color: #f8fafc !important;
        color: #1e2937 !important;
        border: 1px solid #cbd5e1;
    }
</style>
""", unsafe_allow_html=True)

MTZ = ZoneInfo("America/Denver")

# Top Header with Logo
col_logo, col_title = st.columns([1, 4])
with col_logo:
    try:
        st.image("logo.png", width=120)
    except:
        try:
            st.image("logo.jpg", width=120)
        except:
            st.write("🛡️")

with col_title:
    st.title("GUARD RESPONSE PORTAL")
st.caption("Internal • Real-Time Response Tracking • WeAreWatchTower.com")

# Sidebar
st.sidebar.header("Navigation")
page = st.sidebar.radio("Go to", ["Log New Event", "Live Reports", "Performance Charts", "Guard Leaderboard", "Export & Backup"])

# ====================== DATABASE (same as before) ======================
DB_NAME = "watchtower_guard_log.db"

# [Database functions - init_db, parse_time, log_event, get_data, delete_event - remain the same]

# ====================== PAGES ======================
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
            event_dt = parse_time(str(event_date), event_time_str)
            arrival_dt = parse_time(str(event_date), arrival_time_str)
            if event_dt and arrival_dt and log_event(event_dt, guard, arrival_dt, location, event_type, notes):
                st.success("**✅ Event Captured Successfully!**")
                st.balloons()
                st.rerun()

elif page == "Live Reports":
    st.header("Recent Events")
    if not df.empty:
        for _, row in df.iterrows():
            rt = f"{row['response_time_min']:.1f} min" if pd.notna(row.get('response_time_min')) else "Pending"
            cols = st.columns([7, 1, 1])
            with cols[0]:
                st.markdown(f'''
                <div class="event-row">
                    <strong>{row['event_timestamp'].strftime('%Y-%m-%d %I:%M %p')}</strong> — 
                    <strong>{row['dispatched_guard']}</strong> @ {row['location']} 
                    | <strong>{rt}</strong> | {row['event_type']}
                </div>
                ''', unsafe_allow_html=True)
            with cols[1]:
                if st.button("✏️", key=f"e{row['id']}"): st.info("Edit coming soon")
            with cols[2]:
                if st.button("🗑️", key=f"d{row['id']}"):
                    delete_event(row['id'])
                    st.success("Event deleted!")
                    st.rerun()
    else:
        st.info("No events logged yet.")

    st.subheader("Full Table")
    st.dataframe(df, use_container_width=True, hide_index=True)

# Performance Charts and other pages remain the same as before

st.caption("WeAreWatchTower.com • Guard Response System")
