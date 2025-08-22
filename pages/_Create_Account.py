# pages/_Create_Account.py
# -------------------------------------------------------------
# User Registration Page (Hidden from sidebar)
# -------------------------------------------------------------

import streamlit as st





import sqlite3
import bcrypt
from datetime import datetime

st.set_page_config(
    layout="centered"  # 👈 This disables wide mode, keeps it normal
)
# ---------------------------
# Database helpers
# ---------------------------
DB_PATH = "milestone1.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    # The 'users' table is updated to include first and last names.
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash BLOB NOT NULL,
            created_at TEXT NOT NULL
        );
        """
    )
    conn.commit()
    conn.close()


def add_user(first_name: str, last_name: str, email: str, password: str) -> tuple[bool, str]:
    if not email or not password or not first_name or not last_name:
        return False, "All fields are required."
    pw_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    try:
        conn = get_conn()
        # The INSERT query is updated to include first and last names.
        conn.execute(
            "INSERT INTO users(first_name, last_name, email, password_hash, created_at) VALUES(?,?,?,?,?)",
            (first_name.strip(), last_name.strip(), email.strip().lower(), pw_hash, datetime.utcnow().isoformat()),
        )
        conn.commit()
        conn.close()
        return True, "Registration successful."
    except sqlite3.IntegrityError:
        return False, "Email already registered."
    except Exception as e:
        return False, f"Registration failed: {e}"

# ---------------------------
# UI
# ---------------------------
init_db()

st.set_page_config(
    page_title="Create an Account",
    layout="wide"
)

st.title("Create an Account")

with st.form("register_form"):
    col1, col2 = st.columns(2)
    with col1:
        r_first_name = st.text_input("First Name")
    with col2:
        r_last_name = st.text_input("Last Name")

    r_email = st.text_input("New Email")
    r_pwd = st.text_input("New Password", type="password")
    r_confirm_pwd = st.text_input("Confirm Password", type="password")

    if st.form_submit_button("Create Account", use_container_width=True, type="primary"):
        if r_pwd != r_confirm_pwd:
            st.error("Passwords do not match.")
        else:
            # The add_user function call is updated to pass first and last names.
            ok, msg = add_user(r_first_name, r_last_name, r_email, r_pwd)
            if ok:
                st.success(msg + " You can now log in.")
                st.switch_page("pages/Auth.py")
            else:
                st.error(msg)
                
st.markdown("---")
st.markdown("Already have an account?")
if st.button("Go to Login"):
    st.switch_page("pages/Auth.py")
