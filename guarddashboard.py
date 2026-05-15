import streamlit as st
import pandas as pd
from datetime import datetime
import sqlite3
import plotly.express as px
from zoneinfo import ZoneInfo

# ====================== LOGIN ======================
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

# ====================== LIGHT THEME ======================
st.set_page_config(page_title="Watch Tower Guard Portal", page_icon="🛡️", layout="wide")

st.markdown("""
<style>
    .stApp, .main, .block-container { background-color: #ffffff !important; color: #1e2937 !important; }
    h1, h2, h3, label { color: #1e2937 !important; font-weight: 700; }
    .stButton>button { background-color: #db7f36; color: white; font-weight: 600; }
    .stTextInput input, .stSelectbox, .stDateInput input, .stTextArea textarea {
        background-color: #f8fafc !important; color: #1e2937 !important; border: 1px solid #cbd5e1;
    }
    /* Dark Sidebar with Orange */
    .stSidebar { background-color: #1e2937 !important; }
    .stSidebar label, .stSidebar .stRadio label { color: #ffffff !important; }
    .stSidebar h2 { color: #db7f36 !important; }
</style>
""", unsafe_allow_html=True)

MTZ = ZoneInfo("America/Denver")

# ====================== HEADER ======================
col_logo, col_title = st.columns([1, 4])
with col_logo:
    try:
        st.image("logo.png", width=140)
    except:
        try:
            st.image("logo.jpg", width=140)
        except:
            st.write("🛡️")

with col_title:
    st.title("GUARD RESPONSE PORTAL")

st.caption("Internal • Real-Time Response Tracking • WeAreWatchTower.com")

# Sidebar
st.sidebar.header("Navigation")
page = st.sidebar.radio("Go to", ["Log New Event", "Live Reports", "Performance Charts", "Guard Leaderboard", "Export & Backup"])

# ====================== DATABASE ======================
DB_NAME = "watchtower_guard_log.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    conn.execute('''CREATE TABLE IF NOT EXISTS guard_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_timestamp DATETIME NOT NULL,
        dispatched_guard TEXT,
        guard_arrival_timestamp DATETIME NOT NULL,
        location TEXT DEFAULT "Auria",
        event_type TEXT,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.close()

def parse_time(date_str, time_str):
    if not time_str or not time_str.strip(): return None
    try:
        return datetime.strptime(f"{date_str} {time_str.strip()}", "%Y-%m-%d %H:%M").replace(tzinfo=MTZ)
    except:
        try:
            return datetime.strptime(f"{date_str} {time_str.strip()}", "%Y-%m-%d %I:%M %p").replace(tzinfo=MTZ)
        except:
            return None

def log_event(event_dt, guard, arrival_dt, location, event_type, notes):
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.execute('''INSERT INTO guard_events 
            (event_timestamp, dispatched_guard, guard_arrival_timestamp, location, event_type, notes)
            VALUES (?, ?, ?, ?, ?, ?)''', 
            (event_dt.replace(tzinfo=None), guard, arrival_dt.replace(tzinfo=None) if arrival_dt else None, location, event_type, notes))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error saving: {e}")
        return False

def get_data():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM guard_events ORDER BY event_timestamp DESC", conn)
    conn.close()
    if not df.empty:
        df['event_timestamp'] = pd.to_datetime(df['event_timestamp']).dt.tz_localize('UTC').dt.tz_convert(MTZ)
        df['guard_arrival_timestamp'] = pd.to_datetime(df['guard_arrival_timestamp']).dt.tz_localize('UTC').dt.tz_convert(MTZ)
        df['response_time_min'] = (df['guard_arrival_timestamp'] - df['event_timestamp']).dt.total_seconds() / 60
        df['response_time_min'] = df['response_time_min'].abs()
    return df

def delete_event(event_id):
    conn = sqlite3.connect(DB_NAME)
    conn.execute("DELETE FROM guard_events WHERE id = ?", (event_id,))
    conn.commit()
    conn.close()

init_db()
df = get_data()

# ====================== PAGES ======================
if page == "Log New Event":
    st.header("Log New Guard Response")
    with st.form("log_form_2026"):
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
                st.success("**✅ Event Captured Successfully!**")
                st.balloons()
                st.rerun()

elif page == "Live Reports":
    st.header("Recent Events")
    if df.empty:
        st.info("No events logged yet.")
    else:
        for _, row in df.iterrows():
            rt = f"{row['response_time_min']:.1f} min" if pd.notna(row.get('response_time_min')) else "Pending"
            st.markdown(f'''
            <div style="background:#f8fafc; padding:16px; border-radius:8px; margin:8px 0; border:1px solid #e2e8f0;">
                <strong>{row['event_timestamp'].strftime('%Y-%m-%d %I:%M %p')}</strong> — 
                <strong>{row['dispatched_guard']}</strong> @ {row['location']} | 
                <strong>{rt}</strong> | {row['event_type']}
            </div>
            ''', unsafe_allow_html=True)
        st.dataframe(df, use_container_width=True, hide_index=True)

elif page == "Performance Charts":
    st.header("📊 Performance Charts")
    valid = df.dropna(subset=['response_time_min']) if not df.empty else pd.DataFrame()
    if not valid.empty:
        c1, c2, c3 = st.columns(3)
        c1.metric("Avg Response Time", f"{valid['response_time_min'].mean():.1f} min")
        st.plotly_chart(px.line(valid.sort_values('event_timestamp'), x='event_timestamp', y='response_time_min'), use_container_width=True)

st.caption("WeAreWatchTower.com • Guard Response System")
