import streamlit as st
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
import os

st.set_page_config(page_title="Guard Response Portal", layout="wide")

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
MTZ = ZoneInfo("America/Denver")
CSV_FILE = "guard_events.csv"

st.title("🛡️ GUARD RESPONSE PORTAL")
st.caption("WeAreWatchTower.com")

st.sidebar.title("WATCH TOWER")
page = st.sidebar.radio("Navigation", ["Log New Event", "Live Reports"])

# Load or create data
if os.path.exists(CSV_FILE):
    df = pd.read_csv(CSV_FILE)
else:
    df = pd.DataFrame(columns=["event_timestamp", "dispatched_guard", "guard_arrival_timestamp", 
                               "location", "event_type", "notes"])

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
            
            new_row = pd.DataFrame([{
                "event_timestamp": full_event,
                "dispatched_guard": guard,
                "guard_arrival_timestamp": full_arrival,
                "location": location,
                "event_type": event_type,
                "notes": notes
            }])
            
            global df
            df = pd.concat([df, new_row], ignore_index=True)
            df.to_csv(CSV_FILE, index=False)
            
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
