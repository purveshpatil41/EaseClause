# pages/Auth.py
# -------------------------------------------------------------
# User Login Page
# -------------------------------------------------------------

import streamlit as st



import sqlite3
import bcrypt
from datetime import datetime
from forgot_password import show_forgot_password_page # Import the function


# ---------------------------
# Database helpers
# ---------------------------
DB_PATH = "milestone1.db"


def get_conn():
    """Establishes and returns a new database connection."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes the users table if it doesn't exist."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash BLOB NOT NULL,
            created_at TEXT NOT NULL
        );
        """
    )
    conn.commit()
    conn.close()


def verify_user(email: str, password: str):
    """Verifies user credentials by checking the hashed password."""
    conn = get_conn()
    row = conn.execute(
        "SELECT id, first_name, last_name, email, password_hash FROM users WHERE email=?",
        #"SELECT id,  email, password_hash FROM users WHERE email=?",
        (email.strip().lower(),),
    ).fetchone()
    conn.close()
    if not row:
        return None
    try:
        if bcrypt.checkpw(password.encode("utf-8"), row["password_hash"]):
            return {"id": row["id"],"first_name": row["first_name"], "last_name": row["last_name"], "email": row["email"]}
            #return {"id": row["id"], "email": row["email"]}
    except Exception:
        pass
    return None

# ---------------------------
# UI
# ---------------------------
init_db()

st.set_page_config(
    page_title="Login",
    layout="wide"
)

# Initialize a session state variable to control the view
if 'auth_view' not in st.session_state:
    st.session_state.auth_view = 'login'

def go_to_forgot_password():
    st.session_state.auth_view = 'forgot_password'

def go_to_create_account():
    st.switch_page("pages/_Create_Account.py")

# Render the page based on the current view state
if st.session_state.auth_view == 'login':
    if "user" in st.session_state and st.session_state.user:
        st.success(f"You are already logged in as {st.session_state.user['email']}")
        if st.button("Go to Main App"):
            st.switch_page("pages/Main_App.py")
    else:
        st.title("Sign In")

        with st.form("login_form"):
            email = st.text_input("Email", placeholder="your@email.com")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            submitted = st.form_submit_button("Sign In", type="primary", use_container_width=True)
            if submitted:
                user = verify_user(email, password)
                if user:
                    st.session_state.user = user
                    st.success("Login successful. You can now access the app.")
                    st.switch_page("pages/Main_App.py")
                else:
                    st.error("Invalid email or password.")
        st.markdown("Don't have an account?")
        
        # New "Create an account" button
        if st.button("Create an account"):
            st.switch_page("pages/_Create_Account.py")


        st.markdown("---")
        
        st.markdown("Forgot your password?")
        if st.button("Reset Password", on_click=go_to_forgot_password):
            pass # The on_click handler will change the view state
            
elif st.session_state.auth_view == 'forgot_password':
    show_forgot_password_page()
