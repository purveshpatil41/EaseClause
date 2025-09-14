# forgot_password.py
# -------------------------------------------------------------
# Forgot Password Page (Functional)
# -------------------------------------------------------------

import streamlit as st
import sqlite3
import bcrypt
import re

email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

def show_forgot_password_page():
    """
    Renders the forgot password page UI.
    Called from Auth.py
    """
    st.title("🔑 Forgot Password")
    st.markdown("Enter your registered email and set a new password.")

    with st.form("forgot_password_form"):
        email = st.text_input("Email", placeholder="your@email.com")
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")

        submitted = st.form_submit_button("Reset Password", type="primary", use_container_width=True)

        if submitted:
            if not email or not new_password or not confirm_password:
                st.error("⚠️ Please fill in all fields.")
            elif not re.match(email_regex, email):
                st.error("⚠️ Please enter a valid email address.")
            elif new_password != confirm_password:
                st.error("⚠️ Passwords do not match.")
            else:
                try:
                    conn = sqlite3.connect("users.db")
                    c = conn.cursor()

                    hashed_pw = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
                    c.execute("UPDATE users SET password=? WHERE email=?", (hashed_pw, email))
                    conn.commit()

                    if c.rowcount > 0:
                        st.success("✅ Password reset successful! You can now log in with your new password.")
                        st.session_state.auth_view = 'login'
                    else:
                        st.warning("⚠️ Email not found. Please check or sign up.")

                    conn.close()
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

    st.markdown("---")
    st.markdown("Remember your password?")
    if st.button("Go to Login"):
        st.session_state.auth_view = 'login'
