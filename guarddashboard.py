import streamlit as st

st.set_page_config(page_title="Guard Response Portal", layout="wide")

st.title("🛡️ GUARD RESPONSE PORTAL")
st.header("Test Version")

st.write("If you can see this, the app is working.")

if st.button("Test Button"):
    st.success("✅ Button works!")
    st.balloons()

st.caption("WeAreWatchTower.com")
