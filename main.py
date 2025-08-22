

# main.py
# -------------------------------------------------------------
# Landing Page for ClauseEase
# -------------------------------------------------------------

import streamlit as st


st.set_page_config(
    page_title="ClauseEase - Welcome",
    layout="centered"
)

st.title("Welcome to ClauseEase")
st.markdown("""
    Your AI-powered Contract Language Simplifier.
    
    To get started, please sign up or log in.
""")

if st.button("Get Started"):
    st.switch_page("pages/Auth.py")
