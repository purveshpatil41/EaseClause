# forgot_password.py
# -------------------------------------------------------------
# Forgot Password Page (Frontend UI)
# -------------------------------------------------------------

import streamlit as st
import re


email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

def show_forgot_password_page():
    """
    Renders the forgot password page UI.
    This function is imported and called by another script.
    """
    st.set_page_config(
        page_title="Forgot Password",
        layout="wide"
    )

    st.title("Forgot Password")
    st.markdown("Enter your email address to receive a password reset link.")

    # Use a form to group the input and button
    with st.form("forgot_password_form"):
        email = st.text_input("Email", placeholder="your@email.com")
        submitted = st.form_submit_button("Send Reset Link", type="primary", use_container_width=True)

        if submitted:
            if not email:
                st.error("Please enter the email first.")
            #Teammate will handle the backend logic here.
            elif not re.match(email_regex, email):
                st.error("Please enter a valid email address.")
            else:
                st.info(f"If the email '{email}' is registered, you will receive a reset link shortly.")

    st.markdown("---")
    st.markdown("Remember your password?")
    if st.button("Go to Login"):
        # This button needs to change the state back to the login view
        st.session_state.auth_view = 'login'


