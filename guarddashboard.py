import streamlit as st
import pandas as pd
from datetime import datetime
import sqlite3
from zoneinfo import ZoneInfo
import plotly.express as px

st.set_page_config(page_title="Guard Response Portal", layout="wide")
MTZ = ZoneInfo("America/Denver")

st.title("🛡️ GUARD RESPONSE PORTAL")
st.caption("WeAreWatchTower.com")

st.sidebar.title("WATCH TOWER")
page = st.sidebar.radio("Navigation", ["Log New Event", "Live Reports", "Performance Charts"])

# ====================== DATABASE ======================
DB_NAME = "watchtower_guard_log.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("DROP TABLE IF EXISTS guard_events")
    conn.execute('''CREATE TABLE guard_events (
        id INTEGER PRIMARY KEY,
        event_timestamp TEXT,
        remote_monitoring TEXT,
        connection_established TEXT,
        location TEXT,
        event_type TEXT,
        notes TEXT
    )''')
    conn.close()

def log_event(event_time, remote_monitor, connection_time, location, event_type, notes):
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.execute("""INSERT INTO guard_events 
                        (event_timestamp, remote_monitoring, connection_established, location, event_type, notes)
                        VALUES (?, ?, ?, ?, ?, ?)""", 
                     (event_time, remote_monitor, connection_time, location, event_type, notes))
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

# ====================== LOG NEW EVENT ======================
if page == "Log New Event":
    st.header("LOG NEW EVENT")
    with st.form("log_form"):
        col1, col2 = st.columns(2)
        with col1:
            event_date = st.date_input("Event Date", datetime.now(MTZ).date())
            event_time = st.text_input("Event Time", "12:00")
            remote_monitor = st.text_input("Watch Tower Remote Monitoring", "Live Stream")
        with col2:
            connection_time = st.text_input("Watch Tower Connection Established", "12:05")
            location = st.text_input("Location", "Auria")
            event_type = st.selectbox("Event Type", [
                "Alarm Testing", "Power Outage", "Signal Lost", 
                "Test Signal Not Received", "Motion Alarm", 
                "Perimeter Alarm", "Door Contact"
            ])
            notes = st.text_area("Notes")
        
        if st.form_submit_button("✅ Log Event"):
            full_event = f"{event_date} {event_time}"
            full_connection = f"{event_date} {connection_time}"
            if log_event(full_event, remote_monitor, full_connection, location, event_type, notes):
                st.success("**✅ EVENT CAPTURED SUCCESSFULLY!**")
                st.balloons()
                st.rerun()

# ====================== LIVE REPORTS ======================
elif page == "Live Reports":
    st.header("Recent Events")
    df = get_data()
    if df.empty:
        st.info("No events logged yet.")
    else:
        st.success(f"**Total Events Logged: {len(df)}**")
        st.dataframe(df, use_container_width=True, hide_index=True)

# ====================== PERFORMANCE CHARTS ======================
elif page == "Performance Charts":
    st.header("📊 Performance Overview")
    df = get_data()
    
    if df.empty:
        st.info("No events yet. Log some to see charts.")
    else:
        counts = df['event_type'].value_counts()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Events by Type")
            fig_bar = px.bar(
                x=counts.index, 
                y=counts.values,
                labels={'x': 'Event Type', 'y': 'Count'},
                color=counts.index,
                color_discrete_sequence=px.colors.qualitative.Bold
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        
        with col2:
            st.subheader("Distribution")
            fig_pie = px.pie(
                names=counts.index, 
                values=counts.values,
                color=counts.index,
                color_discrete_sequence=px.colors.qualitative.Bold
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        st.subheader("Event Summary")
        for etype, count in counts.items():
            st.write(f"**{etype}** — {count} event{'s' if count > 1 else ''}")

st.caption("WeAreWatchTower.com • Guard Response System")
