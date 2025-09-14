# pages/Main_App.py
# -------------------------------------------------------------
# Main Application - Document Ingestion and Library
# -------------------------------------------------------------

import streamlit as st
import sqlite3
from datetime import datetime

# Optional parsers
try:
    from docx import Document as DocxDocument
except Exception:
    DocxDocument = None

try:
    from PyPDF2 import PdfReader
except Exception:
    PdfReader = None

# ---------------------------
# Database helpers
# ---------------------------
DB_PATH = "users.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS documents(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            filename TEXT,
            mime TEXT,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
    """)
    conn.commit()
    conn.close()

def save_document(user_id: int, content: str, filename: str | None, mime: str | None):
    conn = get_conn()
    conn.execute(
        "INSERT INTO documents(user_id, filename, mime, content, created_at) VALUES(?,?,?,?,?)",
        (user_id, filename, mime, content, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()

def list_documents(user_id: int):
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, filename, mime, content, created_at FROM documents WHERE user_id=? ORDER BY id DESC",
        (user_id,),
    ).fetchall()
    conn.close()
    return rows

def delete_document(doc_id: int, user_id: int):
    conn = get_conn()
    conn.execute("DELETE FROM documents WHERE id=? AND user_id=?", (doc_id, user_id))
    conn.commit()
    conn.close()

# ---------------------------
# Utility: Extract text
# ---------------------------
def read_text_from_upload(uploaded_file) -> tuple[str, str, str]:
    filename = uploaded_file.name
    mime = uploaded_file.type or ""
    name_lower = filename.lower()

    if name_lower.endswith(".txt"):
        text = uploaded_file.read().decode("utf-8", errors="ignore")
        return text, filename, mime

    if name_lower.endswith(".docx"):
        if DocxDocument is None:
            raise RuntimeError("python-docx not installed. Run: pip install python-docx")
        doc = DocxDocument(uploaded_file)
        text = "\n".join([p.text for p in doc.paragraphs])
        return text, filename, mime

    if name_lower.endswith(".pdf"):
        if PdfReader is None:
            raise RuntimeError("PyPDF2 not installed. Run: pip install PyPDF2")
        reader = PdfReader(uploaded_file)
        pages = []
        for p in reader.pages:
            try:
                pages.append(p.extract_text() or "")
            except Exception:
                pages.append("")
        text = "\n".join(pages)
        return text, filename, mime

    try:
        text = uploaded_file.read().decode("utf-8", errors="ignore")
        return text, filename, mime
    except Exception:
        raise RuntimeError("Unsupported file type. Please upload TXT, DOCX, or PDF.")

# ---------------------------
# Logout helper
# ---------------------------
def logout():
    """Clear session and stop execution."""
    st.session_state.clear()
    st.session_state["logged_out"] = True
    st.stop()

# ---------------------------
# Initialize DB
# ---------------------------
init_db()

# ---------------------------
# Handle logged out state
# ---------------------------
if st.session_state.get("logged_out"):
    st.session_state["logged_out"] = False
    st.warning("You have been logged out. Please login again.")
    st.stop()

# ---------------------------
# Check login
# ---------------------------
if "user" not in st.session_state or st.session_state["user"] is None:
    st.warning("Please login to access this page.")
    st.stop()

# ---------------------------
# UI
# ---------------------------
st.title(f"Welcome, {st.session_state.user.get('username', 'User')}!")

# Sidebar logout button
st.sidebar.button("Log out", on_click=logout)

# Tabs
tab_upload, tab_docs = st.tabs(["Upload Document", "Document Library"])

# --- Upload Tab ---
with tab_upload:
    st.markdown("### Upload Document")
    st.write("Paste text or upload a TXT/DOCX/PDF file.")

    paste_text = st.text_area(
        "Paste text here (optional)", height=180,
        placeholder="Paste the content of your legal/policy document..."
    )
    uploaded_file = st.file_uploader("Or upload a file", type=["txt", "docx", "pdf"])

    extracted_text = ""
    filename = None
    mime = None

    if uploaded_file is not None:
        try:
            extracted_text, filename, mime = read_text_from_upload(uploaded_file)
            st.success(f"Parsed **{filename}**")
            with st.expander("Preview extracted text"):
                st.write(extracted_text[:2000] + ("..." if len(extracted_text) > 2000 else ""))
        except Exception as e:
            st.error(str(e))

    if st.button("Save Document"):
        final_text = (paste_text or "").strip() or extracted_text.strip()
        if not final_text:
            st.error("No content to save. Paste text or upload a file first.")
        else:
            save_document(
                st.session_state.user["id"],
                final_text,
                filename or "pasted_text.txt",
                mime or "text/plain"
            )
            st.success("Document saved to your library.")

# --- Library Tab ---
with tab_docs:
    st.markdown("### Document Library")
    docs = list_documents(st.session_state.user["id"])

    if not docs:
        st.info("No documents uploaded yet.")
    else:
        for row in docs:
            with st.container():
                st.markdown(
                    f"<div class='card'><b>#{row['id']}</b> — {row['filename'] or 'Untitled'}"
                    f"<br><span style='font-size:12px;opacity:0.7'>{row['created_at']}</span>"
                    f"<br><br>{(row['content'][:280] + ('...' if len(row['content'])>280 else ''))}</div>",
                    unsafe_allow_html=True,
                )
                cols = st.columns([0.15, 0.15, 0.7])
                if cols[0].button("View", key=f"view_{row['id']}"):
                    st.text_area(
                        f"Document #{row['id']}",
                        row["content"],
                        height=240,
                    )
                if cols[1].button("Delete", key=f"del_{row['id']}"):
                    delete_document(row["id"], st.session_state.user["id"])
                    st.success(f"Deleted document #{row['id']}")
                    st.experimental_rerun()  # works for deletion
