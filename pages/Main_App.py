# pages/Main_App.py
# -------------------------------------------------------------
# Main Application - Document Ingestion, Library, and Simplification
# -------------------------------------------------------------

import streamlit as st
import sqlite3
from datetime import datetime
import os
import re
import textstat 
import json 
import bcrypt 
# Required for LLM integration
import torch 
from transformers import pipeline


# --- CONFIGURATION & SETUP ---

# Optional parsers (for file uploads)
try:
    from docx import Document as DocxDocument
except Exception:
    DocxDocument = None

try:
    from PyPDF2 import PdfReader
except Exception:
    PdfReader = None


# ---------------------------
# Model Loading (CRITICAL for performance)
# ---------------------------
@st.cache_resource
def load_llm_model():
    """Loads the appropriate LLM model and tokenizer only once."""
    # FIX: Using the T5-base model (larger and better for following complex instructions).
    model_name = "google/flan-t5-base"
    # We change the pipeline task back to 'text2text-generation' to enable better instruction following.
    return pipeline("text2text-generation", model=model_name, device=0 if torch.cuda.is_available() else -1)

# Load the model pipeline once
LLM_PIPELINE = load_llm_model()

# ---------------------------
# Core LLM Functions
# ---------------------------
def get_simplified_text(text: str) -> str:
    prompt = f"Rewrite the following legal text in simple English, keeping all meaning:\n\n{text}"
    response = LLM_PIPELINE(prompt, max_length=700, do_sample=False)
    st.write("LLM raw output:", response)
    return response[0]['generated_text'].strip()

def get_summary(text: str) -> str:
    full_prompt = f"Summarize the following legal text in 3-5 bullet points:\n\n{text}"
    response = LLM_PIPELINE(full_prompt, max_length=150, do_sample=False)
    st.write("LLM raw output:", response)
    return response[0]['generated_text'].strip()



# ---------------------------
# Core NLP Functions
# ---------------------------
def clean_text(text: str) -> str:
    """
    Cleans and preprocesses a string for NLP tasks.
    """
    if not text:
        return ""
    
    # Remove special symbols, convert to lowercase, and normalize spacing
    text = re.sub(r'[^a-zA-Z0-9\s\.\',]', '', text, re.UNICODE)
    text = text.lower()
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def calculate_readability(text: str):
    """Calculates Flesch-Kincaid Grade Level and Flesch Reading Ease Score."""
    if not text or len(text.split()) < 10:
        return {"grade": 99.0, "ease": 0.0, "level": "Insufficient Text"}

    grade = textstat.flesch_kincaid_grade(text)
    ease = textstat.flesch_reading_ease(text)

    # Categorize the grade level for easy UI display
    if grade <= 6:
        level = "Easy (Elementary)"
    elif grade <= 8:
        level = "Medium (Middle School)"
    elif grade <= 12:
        level = "Challenging (High School)"
    else:
        level = "Very Difficult (College/Legal)"
        
    return {"grade": grade, "ease": ease, "level": level}


# ---------------------------
# Database helpers (Shared across app)
# ---------------------------
DB_PATH = "users.db" 

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    
    # 1. Documents Table (for raw file storage)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS documents(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            filename TEXT,
            mime TEXT,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        """
    )
    # 2. Simplification Results Table (The new central table for saving analysis)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS simplification_results(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            original_text TEXT NOT NULL,
            simplified_text TEXT NOT NULL,
            scores_before TEXT NOT NULL,
            scores_after TEXT NOT NULL,
            summary TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        """
    )
    conn.commit()
    conn.close()

def save_simplification_result(user_id: int, filename: str, original_text: str, simplified_text: str, scores_before: dict, scores_after: dict, summary: str):
    """Saves the full comparison result set to the new simplification_results table."""
    conn = get_conn()
    conn.execute(
        """
        INSERT INTO simplification_results(user_id, filename, original_text, simplified_text, scores_before, scores_after, summary, created_at) 
        VALUES(?,?,?,?,?,?,?,?)
        """,
        (
            user_id, 
            filename,
            original_text,
            simplified_text,
            json.dumps(scores_before), 
            json.dumps(scores_after),
            summary, 
            datetime.utcnow().isoformat()
        ),
    )
    conn.commit()
    conn.close()

def list_simplification_results(user_id: int):
    """Lists all saved simplification results for the current user."""
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, filename, scores_before, created_at FROM simplification_results WHERE user_id=? ORDER BY id DESC",
        (user_id,),
    ).fetchall()
    conn.close()
    return rows

def get_single_result(result_id: int, user_id: int):
    """Retrieves a single detailed result for the full view mode."""
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM simplification_results WHERE id=? AND user_id=?",
        (result_id, user_id),
    ).fetchone()
    conn.close()
    
    if row:
        result = dict(row)
        result['scores_before'] = json.loads(result['scores_before'])
        result['scores_after'] = json.loads(result['scores_after'])
        return result
    return None


# ---------------------------
# Utility: extract text (File Readers)
# ---------------------------
def read_text_from_upload(uploaded_file) -> tuple[str, str, str]:
    """
    Returns (text, filename, mime) from various uploaded file types.
    """
    filename = uploaded_file.name
    mime = uploaded_file.type or ""
    name_lower = filename.lower()

    if name_lower.endswith(".txt"):
        text = uploaded_file.read().decode("utf-8", errors="ignore")
        return text, filename, mime

    if name_lower.endswith(".docx"):
        if DocxDocument is None:
            raise RuntimeError("python-docx not installed. Run: uv pip install python-docx")
        doc = DocxDocument(uploaded_file)
        text = "\n".join([p.text for p in doc.paragraphs])
        return text, filename, mime

    if name_lower.endswith(".pdf"):
        if PdfReader is None:
            raise RuntimeError("PyPDF2 not installed. Run: uv pip install PyPDF2")
        reader = PdfReader(uploaded_file)
        pages = []
        for p in reader.pages:
            try:
                pages.append(p.extract_text() or "")
            except Exception:
                pages.append("")
        text = "\n".join(pages)
        return text, filename, mime

    raise RuntimeError("Unsupported file type. Please upload TXT, DOCX, or PDF.")


# ---------------------------
# App Logic
# ---------------------------
init_db()

# --- Initial Model Loading Block (Runs only once, shows spinner) ---
try:
    with st.spinner("Loading AI Model (This only takes a moment the first time)..."):
        LLM_PIPELINE = load_llm_model()
except Exception as e:
    st.error(f"Failed to load AI model. Please ensure 'transformers' and 'torch' are installed. Error: {e}")
    st.stop()
# -------------------------------------------------------------------


# Security Check: Stop if user is not logged in
if "user" not in st.session_state or st.session_state.user is None:
    st.warning("Please login to access this page.")
    st.stop()


# Initialize state for full result view
if 'view_result_id' not in st.session_state:
    st.session_state.view_result_id = None


# Main UI Header
user_display_name = st.session_state.user.get('first_name', st.session_state.user.get('email', 'User'))
st.title(f"Welcome, {user_display_name}")

st.button("Log out", on_click=lambda: st.switch_page("main.py"))

st.markdown("## Main Application")

# --- Conditional Display: Full Result View or Tabs ---
if st.session_state.view_result_id is not None:
    # ----------------------------------------------------
    # FULL RESULT VIEW MODE
    # ----------------------------------------------------
    result_data = get_single_result(st.session_state.view_result_id, st.session_state.user["id"])
    
    st.markdown(f"### Detailed Analysis: {result_data['filename']}")
    
    # Back button logic
    if st.button("← Back to Library"):
        st.session_state.view_result_id = None
        st.rerun()

    if result_data:
        # Replicate the result display logic for full page view
        col_orig, col_simp = st.columns(2)
        
        with col_orig:
            st.markdown("#### Original Document")
            st.info(f"**Readability (Before):** Grade {result_data['scores_before']['grade']:.1f} ({result_data['scores_before']['level']})")
            st.text_area("Original Text", result_data['original_text'], height=300, disabled=True)
            
        with col_simp:
            st.markdown("#### Simplified Output")
            st.success(f"**Readability (After):** Grade {result_data['scores_after']['grade']:.1f} ({result_data['scores_after']['level']})")
            st.text_area("Simplified Text", result_data['simplified_text'], height=300, disabled=True)
            
        st.markdown("---")
        st.markdown("#### Summary")
        st.write(result_data['summary'])
    else:
        st.error("Result not found.")

else:
    # ----------------------------------------------------
    # TAB VIEW MODE
    # ----------------------------------------------------
    tab_upload, tab_docs = st.tabs(["Simplify New Document", "Document Library"])

    # --- TAB 1: Document Input & Simplification ---
    with tab_upload:
        st.markdown("### Document Input")
        
        # Input Selector (Radio Buttons)
        input_mode = st.radio(
            "How would you like to input the document?",
            ["Paste Text", "Upload Document"],
            index=0, 
            horizontal=True,
            key="main_app_input_mode"
        )

        # Variables for text content
        raw_text = ""
        uploaded_file = None
        extracted_text = ""
        filename_for_save = "Pasted Contract" 
        
        # Conditional UI based on radio button choice
        if input_mode == "Paste Text":
            raw_text = st.text_area("Paste legal/policy document text here", height=300, placeholder="Paste the content of your document...")
            
        elif input_mode == "Upload Document":
            uploaded_file = st.file_uploader("Upload a file", type=["txt", "docx", "pdf"])
            
        
        # STEP 1: Process Text from Uploaded File (if any)
        if uploaded_file is not None:
            try:
                extracted_text, filename_for_save, mime = read_text_from_upload(uploaded_file)
                st.success(f"Parsed **{filename_for_save}** successfully.")
                with st.expander("Preview Extracted Raw Text"):
                    st.text_area("Raw Text", extracted_text[:2000], height=100)

            except Exception as e:
                st.error(f"Error parsing file. Ensure the required libraries are installed: {str(e)}")

        # Final text source (prioritize extracted, then pasted)
        final_raw_text = (raw_text or extracted_text).strip()


        # ----------------------------------------------------
        # STEP 2: The Core "Simplify" Button
        # ----------------------------------------------------
        # RESERVES A SPOT FOR DYNAMIC UPDATES
        status_message_placeholder = st.empty()
        
        if st.button("Simplify Document", type="primary", use_container_width=True):
            if not final_raw_text or len(final_raw_text.split()) < 10:
                st.error("Please provide at least 10 words of text by pasting or uploading a document.")
            else:
                # 1. Clean the text
                cleaned_text = clean_text(final_raw_text)
                
                # 2. Calculate Readability Score (Before)
                score_before = calculate_readability(cleaned_text)

                # --- FIX: Show Loading Message Immediately ---
                status_message_placeholder.info("Processing document with T5-Base. This may take up to 20 seconds...")
                
                # 3. Get Simplified Text (LLM runs here)
                simplified_text = get_simplified_text(final_raw_text)
                summary = get_summary(final_raw_text)
                
                # 4. Calculate Readability Score (After)
                score_after = calculate_readability(simplified_text) 

                # --- SAVE LOGIC ---
                save_simplification_result(
                    st.session_state.user["id"],
                    filename_for_save,
                    final_raw_text,
                    simplified_text,
                    score_before,
                    score_after,
                    summary
                )

                # Save the results to session state for immediate display
                st.session_state.simplification_results = {
                    'original': final_raw_text,
                    'cleaned': cleaned_text,
                    'simplified': simplified_text,
                    'score_before': score_before,
                    'score_after': score_after,
                    'summary': summary
                }
                
                # --- CRITICAL FIX: Order Changed ---
                # 1. Clear the message box
                status_message_placeholder.empty() 
                
                # 2. Show the final success message
                st.success("Simplification complete! Scroll down to see results.")
                
                # 3. Force the page to restart to run the display logic
                st.rerun() 

        # ----------------------------------------------------
        # STEP 3: Display Results Panel (Post-Rerun)
        # ----------------------------------------------------
        if 'simplification_results' in st.session_state:
            results = st.session_state.simplification_results
            
            st.markdown("### Simplification Results")
            
            col_orig, col_simp = st.columns(2)
            
            with col_orig:
                st.markdown("#### Original Document")
                st.info(f"**Readability (Before):** Grade {results['score_before']['grade']:.1f} ({results['score_before']['level']})")
                st.text_area("Original Text", results['original'], height=300, disabled=True)
                
            with col_simp:
                st.markdown("#### Simplified Output")
                st.success(f"**Readability (After):** Grade {results['score_after']['grade']:.1f} ({results['score_after']['level']})")
                st.text_area("Simplified Text", results['simplified'], height=300, disabled=True)
                
            st.markdown("---")
            st.markdown("#### Summary")
            st.write(results['summary'])
            

    # --- TAB 2: Document Library ---
    with tab_docs:
        st.markdown("### Document Library")
        
        # List all simplification results
        docs = list_simplification_results(st.session_state.user["id"])
        
        if not docs:
            st.info("No simplified documents saved yet.")
        else:
            for row in docs:
                scores = json.loads(row['scores_before']) 
                
                with st.container(border=True):
                    col1, col2 = st.columns([0.7, 0.3])
                    
                    with col1:
                        st.markdown(f"**{row['filename']}** (`ID: {row['id']}`)")
                        st.caption(f"Simplified on: {row['created_at']}")
                        st.write(f"**Original Grade Level:** **{scores['grade']:.1f}** ({scores['level']})")
                        
                    with col2:
                        if st.button("View Full Result", key=f"view_result_{row['id']}"):
                            st.session_state.view_result_id = row['id']
                            st.rerun()
