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
    .stApp { background-color: #0a0f1c; color: #e2e8f0; font-family: 'Helvetica', Arial, sans-serif; }
    .stButton>button { background-color: #f97316; color: white; border-radius: 6px; font-weight: 600; padding: 8px 16px; }
    h1 { color: #ffffff; font-weight: 700; letter-spacing: -0.5px; }
    h2, h3 { color: #f1f5f9; }
    .event-row { background-color: #1e2937; padding: 16px; border-radius: 8px; margin-bottom: 12px; }
    .stTextInput > div > div > input, .stSelectbox, .stDateInput { background-color: #1e2937 !important; color: #e2e8f0 !important; }
</style>
""", unsafe_allow_html=True)

MTZ = ZoneInfo("America/Denver")

# Sidebar Logo
try:
    st.sidebar.image("logo.png", width=200)
except:
    try:
        st.sidebar.image("logo.jpg", width=200)
    except:
        st.sidebar.markdown("**🛡️ WATCH TOWER**")

st.sidebar.header("Navigation")
page = st.sidebar.radio("Go to", ["Log New Event", "Live Reports", "Performance Charts", "Guard Leaderboard", "Export & Backup"])

st.title("GUARD RESPONSE PORTAL")
st.caption("Internal • Real-Time Response Tracking • WeAreWatchTower.com")

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
    except:
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
                st.success("✅ Event logged successfully!")
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
                    st.success("Deleted!")
                    st.rerun()
    else:
        st.info("No events logged yet.")

    st.subheader("Full Table")
    st.dataframe(df, use_container_width=True, hide_index=True)

# (Performance Charts, Leaderboard, Export pages remain the same as before)

elif page == "Performance Charts":
    st.header("📊 Guard Response Performance")
    valid_df = df.dropna(subset=['response_time_min']) if not df.empty else pd.DataFrame()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Completed", len(valid_df))
    if not valid_df.empty:
        c2.metric("Avg Response", f"{valid_df['response_time_min'].mean():.1f} min")
        c3.metric("Fastest", f"{valid_df['response_time_min'].min():.1f} min")
        c4.metric("Slowest", f"{valid_df['response_time_min'].max():.1f} min")

    st.subheader("Response Time Trend")
    if not valid_df.empty:
        fig = px.line(valid_df.sort_values('event_timestamp'), x='event_timestamp', y='response_time_min', markers=True)
        fig.add_hline(y=8, line_dash="dash", line_color="#f97316", annotation_text="8 min Target")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Event Type Breakdown")
    if not df.empty:
        type_counts = df['event_type'].value_counts()
        c1, c2 = st.columns(2)
        with c1:
            fig_pie = px.pie(names=type_counts.index, values=type_counts.values, title="Event Types", color_discrete_sequence=px.colors.sequential.Oranges)
            st.plotly_chart(fig_pie, use_container_width=True)
        with c2:
            fig_bar = px.bar(x=type_counts.index, y=type_counts.values, title="Count by Type", color=type_counts.values, color_continuous_scale="Oranges")
            st.plotly_chart(fig_bar, use_container_width=True)

elif page == "Guard Leaderboard":
    st.header("🏆 Guard Leaderboard")
    valid_df = df.dropna(subset=['response_time_min']) if not df.empty else pd.DataFrame()
    if not valid_df.empty:
        lb = valid_df.groupby('dispatched_guard').agg(
            responses=('id','count'),
            avg_response=('response_time_min','mean'),
            best=('response_time_min','min'),
            worst=('response_time_min','max')
        ).round(1).sort_values('avg_response')
        st.dataframe(lb, use_container_width=True)

elif page == "Export & Backup":
    st.header("Export & Backup")
    if not df.empty:
        if st.button("📥 Download Full Excel Backup"):
            df.to_excel("WatchTower_Guard_Backup.xlsx", index=False)
            st.success("✅ Backup downloaded!")

st.caption("WeAreWatchTower.com • Guard Response System")
