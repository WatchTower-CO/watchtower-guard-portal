import streamlit as st
import pandas as pd
from datetime import datetime
import sqlite3
from zoneinfo import ZoneInfo

# ====================== LOGIN ======================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("Watch Tower Guard Portal Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username == "Admin" and password == "WATCHtower123!@":
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Incorrect credentials")
    st.stop()

# ====================== SETUP ======================
st.set_page_config(page_title="Guard Response Portal", layout="wide")
MTZ = ZoneInfo("America/Denver")

st.title("🛡️ GUARD RESPONSE PORTAL")
st.caption("WeAreWatchTower.com")

st.sidebar.title("WATCH TOWER")
page = st.sidebar.radio("Navigation", ["Log New Event", "Live Reports"])

# ====================== DATABASE ======================
DB_NAME = "watchtower_guard_log.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("DROP TABLE IF EXISTS guard_events")
    conn.execute('''CREATE TABLE guard_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_timestamp TEXT,
        dispatched_guard TEXT,
        guard_arrival_timestamp TEXT,
        location TEXT,
        event_type TEXT,
        notes TEXT
    )''')
    conn.close()

def log_event(event_time, guard, arrival_time, location, event_type, notes):
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.execute("""INSERT INTO guard_events 
                        (event_timestamp, dispatched_guard, guard_arrival_timestamp, location, event_type, notes)
                        VALUES (?, ?, ?, ?, ?, ?)""", 
                     (event_time, guard, arrival_time, location, event_type, notes))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Save error: {e}")
        return False

def get_data():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM guard_events ORDER BY id DESC", conn)
    conn.close()
    return df

init_db()
df = get_data()

# ====================== LOG NEW EVENT ======================
if page == "Log New Event":
    st.header("LOG NEW EVENT")
    with st.form("log_form"):
        col1, col2 = st.columns(2)
        with col1:
            event_date = st.date_input("Event Date", datetime.now(MTZ).date())
            event_time = st.text_input("Event Time", "12:00")
            guard = st.text_input("Dispatched Guard", "Teddy")
        with col2:
            arrival_time = st.text_input("Guard Arrival Time", "12:05")
            location = st.text_input("Location", "Auria")
            event_type = st.selectbox("Event Type", [
                "Alarm", "False Alarm", "Alarm Testing", "User Error",
                "Power Outage", "Signal Lost", "Motion", "Door Contact", 
                "Perimeter Breach", "Other"
            ])
            notes = st.text_area("Notes")
        
        if st.form_submit_button("✅ Log Event"):
            full_event = f"{event_date} {event_time}"
            full_arrival = f"{event_date} {arrival_time}"
            if log_event(full_event, guard, full_arrival, location, event_type, notes):
                st.success("**✅ EVENT CAPTURED SUCCESSFULLY!**")
                st.balloons()
                st.rerun()

# ====================== LIVE REPORTS ======================
elif page == "Live Reports":
    st.header("Recent Events")
    if df.empty:
        st.info("No events logged yet.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)

st.caption("WeAreWatchTower.com • Guard Response System")
