import streamlit as st

st.set_page_config(page_title="Guard Response Portal", layout="wide")

st.title("🛡️ GUARD RESPONSE PORTAL")
st.write("**Test Version** - If you can see this, the app is working.")

st.header("Login Test")
username = st.text_input("Username", "Admin")
password = st.text_input("Password", "WATCHtower123!@", type="password")

if st.button("Login"):
    if username == "Admin" and password == "WATCHtower123!@":
        st.success("Logged in successfully!")
        st.balloons()
    else:
        st.error("Wrong credentials")

st.caption("WeAreWatchTower.com • Test Version")
