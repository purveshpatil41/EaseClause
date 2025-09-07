# pages/Readability.py
# -------------------------------------------------------------
# Contract Readability Analysis (Milestone 2)
# Person D's Contribution
# -------------------------------------------------------------

import streamlit as st
import spacy
import textstat
import matplotlib.pyplot as plt

# -------------------------------------------------------------
# Page Config
# -------------------------------------------------------------
st.set_page_config(page_title="ClauseEase - Readability", layout="wide")

# -------------------------------------------------------------
# Title & Description
# -------------------------------------------------------------
st.title("📊 Contract Readability Analysis")
st.markdown("""
Paste your contract or paragraph below to check its readability.
This tool uses **spaCy** for preprocessing and **readability metrics** like:
- Flesch Reading Ease  
- Flesch-Kincaid Grade Level  
- Gunning Fog Index  
""")

# -------------------------------------------------------------
# Text Input
# -------------------------------------------------------------
user_text = st.text_area("✍️ Enter contract text:", height=200, placeholder="Paste your contract text here...")

# -------------------------------------------------------------
# Analyze Button
# -------------------------------------------------------------
if st.button("Analyze Readability"):
    if user_text.strip():
        # -------- Preprocessing with spaCy --------
        nlp = spacy.load("en_core_web_sm")
        doc = nlp(user_text)

        sentences = list(doc.sents)
        tokens = [t.text for t in doc if t.is_alpha]

        # -------- Readability Scores --------
        flesch = textstat.flesch_reading_ease(user_text)
        fk_grade = textstat.flesch_kincaid_grade(user_text)
        gunning_fog = textstat.gunning_fog(user_text)

        # -------- Difficulty Label --------
        if flesch > 60:
            difficulty = "✅ Easy to Read"
            color = "green"
        elif flesch > 30:
            difficulty = "⚖️ Moderate Difficulty"
            color = "orange"
        else:
            difficulty = "❌ Hard to Read"
            color = "red"

        # -------------------------------------------------------------
        # Display Results
        # -------------------------------------------------------------
        st.subheader("📈 Readability Scores")

        col1, col2, col3 = st.columns(3)
        col1.metric("Flesch Reading Ease", f"{flesch:.1f}")
        col2.metric("Flesch-Kincaid Grade", f"{fk_grade:.1f}")
        col3.metric("Gunning Fog Index", f"{gunning_fog:.1f}")

        st.markdown(f"<h3 style='color:{color};'>Overall Difficulty: {difficulty}</h3>", unsafe_allow_html=True)

        # -------------------------------------------------------------
        # Extra Info
        # -------------------------------------------------------------
        st.info(f"📌 Sentences: {len(sentences)} | Words: {len(tokens)}")

        # -------------------------------------------------------------
        # Visualization: Bar Chart
        # -------------------------------------------------------------
        st.subheader("📊 Visual Comparison")
        scores = {
            "Flesch Reading Ease": flesch,
            "FK Grade": fk_grade,
            "Gunning Fog": gunning_fog
        }
        fig, ax = plt.subplots()
        ax.bar(scores.keys(), scores.values(), color=["blue", "purple", "teal"])
        ax.set_ylabel("Score")
        ax.set_title("Readability Metrics")
        st.pyplot(fig)

    else:
        st.warning("⚠️ Please paste some text to analyze.")
