import streamlit as st
from datetime import datetime

st.set_page_config(page_title="Guard Response Portal", layout="wide")

# Simple Login
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
    st.stop()

# Main App
st.title("🛡️ GUARD RESPONSE PORTAL")
st.write("Test version - If you can see this, the app is loading.")

st.header("LOG NEW EVENT")
event_type = st.selectbox("Event Type", ["Alarm", "Power Outage", "Signal Lost", "Other"])
guard = st.text_input("Dispatched Guard", "Teddy")
location = st.text_input("Location", "Auria")
notes = st.text_area("Notes")

if st.button("✅ Log Event"):
    st.success("**✅ EVENT CAPTURED SUCCESSFULLY!**")
    st.balloons()

st.caption("WeAreWatchTower.com • Test Version")
