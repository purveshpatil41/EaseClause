
# backend.py
import sqlite3
import bcrypt
from datetime import datetime
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

DB_PATH = "users.db"

# -----------------------------
# Database initialization
# -----------------------------
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # Users table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT,
            last_name TEXT,
            email TEXT UNIQUE,
            password BLOB,
            is_admin INTEGER DEFAULT 0
        )
    """)

    # Simplifications table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS simplifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT,
            level TEXT,
            original_text TEXT,
            simplified_text TEXT,
            timestamp TEXT
        )
    """)

    # Documents table (linked by user_email)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            filename TEXT,
            mime TEXT,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()
    print("Database initialized successfully.")

# -----------------------------
# User management functions
# -----------------------------
def add_user(email, password, first_name, last_name, is_admin=0):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email=?", (email,))
    if cur.fetchone():
        conn.close()
        return False
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    cur.execute(
        "INSERT INTO users (email, password, first_name, last_name, is_admin) VALUES (?, ?, ?, ?, ?)",
        (email, hashed, first_name, last_name, is_admin)
    )
    conn.commit()
    conn.close()
    return True

def get_user(email):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email=?", (email,))
    user = cur.fetchone()
    conn.close()
    return user

def verify_user(email, password):
    user = get_user(email)
    if user and bcrypt.checkpw(password.encode(), user["password"]):
        return True
    return False

def is_admin(email):
    user = get_user(email)
    return user and user["is_admin"] == 1

def get_all_users():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, first_name, last_name, email, is_admin FROM users")
    users = cur.fetchall()
    conn.close()
    return users

def update_password(email, new_password):
    conn = get_conn()
    hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt())
    conn.execute("UPDATE users SET password=? WHERE email=?", (hashed, email))
    conn.commit()
    conn.close()

# -----------------------------
# Multi-Level Simplification (T5 model)
# -----------------------------
model_name = "t5-small"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

def simplify_text(text, level):
    prefix = {"Basic": "simplify: ", "Intermediate": "simplify: ", "Advanced": "simplify: "}.get(level, "simplify: ")
    inputs = tokenizer(prefix + text, return_tensors="pt", max_length=512, truncation=True)
    outputs = model.generate(**inputs, max_length=512, num_beams=4)
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

# -----------------------------
# Logging simplifications
# -----------------------------
def log_simplification(user_email, level, original_text, simplified_text):
    conn = get_conn()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        "INSERT INTO simplifications (user_email, level, original_text, simplified_text, timestamp) VALUES (?, ?, ?, ?, ?)",
        (user_email, level, original_text, simplified_text, timestamp)
    )
    conn.commit()
    conn.close()

def get_user_logs(user_email):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT level, original_text, simplified_text, timestamp FROM simplifications WHERE user_email=? ORDER BY timestamp DESC",
        (user_email,)
    )
    logs = cur.fetchall()
    conn.close()
    return logs

# -----------------------------
# Document functions
# -----------------------------
def get_user_documents(user_email):
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, filename, mime, content, created_at FROM documents WHERE user_email=? ORDER BY created_at DESC",
        (user_email,)
    ).fetchall()
    conn.close()
    return rows

# -----------------------------
# Setup default admin
# -----------------------------
def add_admin(email="admin@example.com", password="adminpass"):
    if get_user(email):
        print("Admin already exists.")
        return
    add_user(email, password, "Admin", "User", is_admin=1)
    print(f"Admin user created: {email} / {password}")

def setup():
    init_db()
    add_admin()



