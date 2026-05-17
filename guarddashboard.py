import streamlit as st

st.set_page_config(page_title="Test", layout="wide")

st.title("🛡️ GUARD RESPONSE PORTAL - TEST VERSION")
st.write("If you can see this text, the app is working.")

st.header("Quick Test")
if st.button("Click Me"):
    st.success("✅ Button works!")
    st.balloons()

st.caption("WeAreWatchTower.com • Test")
