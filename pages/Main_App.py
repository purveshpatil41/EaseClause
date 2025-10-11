# pages/Main_App.py
# -------------------------------------------------------------
# Main Application - Document Ingestion and Library
# -------------------------------------------------------------

import streamlit as st
import sqlite3
from datetime import datetime
from backend import DB_PATH, init_db
import os

# ---------------------------
# Optional parsers
# ---------------------------
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
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def save_document(user_email: str, content: str, filename: str | None, mime: str | None):
    conn = get_conn()
    conn.execute(
        "INSERT INTO documents(user_email, filename, mime, content, created_at) VALUES(?,?,?,?,?)",
        (user_email, filename, mime, content, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()

def list_documents(user_email: str):
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, filename, mime, content, created_at FROM documents WHERE user_email=? ORDER BY id DESC",
        (user_email,),
    ).fetchall()
    conn.close()
    return rows

def delete_document(doc_id: int, user_email: str):
    conn = get_conn()
    conn.execute("DELETE FROM documents WHERE id=? AND user_email=?", (doc_id, user_email))
    conn.commit()
    conn.close()

# ---------------------------
# Utility: extract text
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
# Initialize DB
# ---------------------------
init_db()

# ---------------------------
# Require login
# ---------------------------
if "user" not in st.session_state or st.session_state.user is None:
    st.warning("Please login to access this page.")
    st.stop()

# Welcome message
user_email = st.session_state.user["email"]
st.title(f"Welcome, {user_email}!")

# Logout
if st.button("Log out"):
    st.session_state.clear()
    st.experimental_rerun()

st.markdown("## Main Application")
tab_upload, tab_docs = st.tabs(["Upload Document", "Document Library"])

# ---------------------------
# Upload Tab
# ---------------------------
with tab_upload:
    st.markdown("### Upload Document")
    st.write("You can paste text or upload a TXT/DOCX/PDF file.")

    paste_text = st.text_area(
        "Paste text here (optional)",
        height=180,
        placeholder="Paste the content of your legal/policy document...",
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
        final_text = (paste_text or "").strip()
        if not final_text and extracted_text:
            final_text = extracted_text.strip()
        if not final_text:
            st.error("No content to save. Paste text or upload a file first.")
        else:
            save_document(
                user_email,
                final_text,
                filename or "pasted_text.txt",
                mime or "text/plain",
            )
            st.success("Document saved to your library.")

# ---------------------------
# Library Tab
# ---------------------------
with tab_docs:
    st.markdown("### Document Library")
    docs = list_documents(user_email)
    if not docs:
        st.info("No documents uploaded yet.")
    else:
        for row in docs:
            with st.container():
                st.markdown(
                    f"<div class='card'><b>#{row['id']}</b> — {row['filename'] or 'Untitled'} "
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
                    delete_document(row["id"], user_email)
                    st.success(f"Deleted document #{row['id']}")
                    st.experimental_rerun()

