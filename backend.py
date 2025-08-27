import sqlite3
import bcrypt

# --- Initialize DB ---
def init_db():
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    # The users table is updated to use 'email' as the UNIQUE identifier
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT,
            last_name TEXT,
            email TEXT UNIQUE,
            password BLOB
        )
    """)
    conn.commit()
    conn.close()

# --- Add new user ---
def add_user(email, password, first_name, last_name):
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    # check if email exists
    cur.execute("SELECT * FROM users WHERE email=?", (email,))
    if cur.fetchone():
        conn.close()
        return False  # email already exists

    # hash password
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

    # insert new user
    cur.execute("INSERT INTO users (email, password, first_name, last_name) VALUES (?, ?, ?, ?)",
                (email, hashed, first_name, last_name))
    conn.commit()
    conn.close()
    return True

# --- Get user by email ---
def get_user(email):
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email=?", (email,))
    data = cur.fetchone()
    conn.close()
    return data

# --- Update password ---
def update_password(email, new_password):
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt())
    cur.execute("UPDATE users SET password=? WHERE email=?", (hashed, email))
    conn.commit()
    conn.close()
