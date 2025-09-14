# pages/Readability.py
# -------------------------------------------------------------
# Contract Readability Analysis (Milestone 2)
# Person D's Contribution
# -------------------------------------------------------------

import streamlit as st
import spacy
import textstat
import matplotlib.pyplot as plt
import string

# -------------------------------------------------------------
# Page Config
# -------------------------------------------------------------
st.set_page_config(page_title="ClauseEase - Readability", layout="wide")

# -------------------------------------------------------------
# Title & Description
# -------------------------------------------------------------
st.markdown("<h1 style='text-align:center; color:#4CAF50;'>📊 Contract Readability Analysis</h1>", unsafe_allow_html=True)
st.markdown("""
Welcome to the **ClauseEase Readability Module**!  
Paste your contract or paragraph below to check its **readability level**.  

This tool uses **spaCy** for preprocessing and calculates readability metrics like:
- 🟦 Flesch Reading Ease  
- 🟪 Flesch-Kincaid Grade Level  
- 🟩 Gunning Fog Index  
""")

st.markdown("---")

# -------------------------------------------------------------
# Text Input
# -------------------------------------------------------------
user_text = st.text_area("✍️ Paste your contract text:", height=200, placeholder="Enter contract or policy text here...")

# -------------------------------------------------------------
# Analyze Button
# -------------------------------------------------------------
if st.button("🚀 Analyze Readability"):
    if user_text.strip():
        # -------- Preprocessing with spaCy --------
        nlp = spacy.load("en_core_web_sm")
        doc = nlp(user_text)

        sentences = list(doc.sents)
        tokens = [t.text for t in doc if t.is_alpha]

        # Cleaned preprocessed text (lowercase, no stopwords/punct)
        tokens_cleaned = [t.text.lower() for t in doc if t.is_alpha and not t.is_stop]
        preprocessed_text = " ".join(tokens_cleaned)

        # Punctuation count + breakdown
        punctuations = [t.text for t in doc if t.is_punct]
        punct_count = len(punctuations)
        punct_breakdown = {}
        for p in punctuations:
            punct_breakdown[p] = punct_breakdown.get(p, 0) + 1

        # -------- Readability Scores --------
        flesch = textstat.flesch_reading_ease(user_text)
        fk_grade = textstat.flesch_kincaid_grade(user_text)
        gunning_fog = textstat.gunning_fog(user_text)

        # -------- Difficulty Label --------
        if flesch > 60:
            difficulty = "✅ Easy to Read"
            color = "#4CAF50"
        elif flesch > 30:
            difficulty = "⚖️ Moderate Difficulty"
            color = "#FFA500"
        else:
            difficulty = "❌ Hard to Read"
            color = "#FF4500"

        # -------------------------------------------------------------
        # Display Results
        # -------------------------------------------------------------
        st.subheader("📈 Readability Scores")

        col1, col2, col3 = st.columns(3)
        col1.metric("🟦 Flesch Reading Ease", f"{flesch:.1f}")
        col2.metric("🟪 FK Grade Level", f"{fk_grade:.1f}")
        col3.metric("🟩 Gunning Fog Index", f"{gunning_fog:.1f}")

        st.markdown(f"<h3 style='color:{color}; text-align:center;'>{difficulty}</h3>", unsafe_allow_html=True)

        # -------------------------------------------------------------
        # Extra Stats in Highlight Boxes
        # -------------------------------------------------------------
        col4, col5, col6 = st.columns(3)
        col4.metric("📝 Sentences", len(sentences))
        col5.metric("🔤 Words", len(tokens))
        col6.metric("✒️ Punctuations", punct_count)

        st.markdown("---")

        # -------------------------------------------------------------
        # Unified Analysis Report
        # -------------------------------------------------------------
        st.subheader("📑 Detailed Analysis Report")

        # Preprocessed text
        st.markdown("### 🧹 Preprocessed Text (Cleaned & Tokenized)")
        st.write(preprocessed_text if preprocessed_text else "No tokens found.")

        # Sentence breakdown
        st.markdown("### 📝 Sentence-by-Sentence Breakdown")
        for i, sent in enumerate(sentences, start=1):
            st.write(f"**{i}.** {sent.text.strip()}")

        # Punctuation breakdown
        st.markdown("### 🔎 Punctuation Breakdown")
        if punct_breakdown:
            for p, count in punct_breakdown.items():
                st.write(f"- `{p}` : {count}")
        else:
            st.write("No punctuation found.")

        st.markdown("---")

        # -------------------------------------------------------------
        # Visualization: Bar Chart
        # -------------------------------------------------------------
        st.subheader("📊 Visual Comparison of Scores")
        scores = {
            "Flesch Reading Ease": flesch,
            "FK Grade": fk_grade,
            "Gunning Fog": gunning_fog
        }
        fig, ax = plt.subplots()
        ax.bar(scores.keys(), scores.values(), color=["#2196F3", "#9C27B0", "#009688"])
        ax.set_ylabel("Score")
        ax.set_title("Readability Metrics")
        st.pyplot(fig)

    else:
        st.warning("⚠️ Please paste some text to analyze.")
