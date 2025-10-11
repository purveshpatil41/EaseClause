import json
import re
import streamlit as st

# ---------------------------
# Load glossary terms
# ---------------------------
def load_glossary(path="data/glossary.json"):
    """Load glossary terms from a JSON file."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            glossary = json.load(f)
        return glossary
    except FileNotFoundError:
        st.warning("⚠️ Glossary file not found at data/glossary.json.")
        return {}
    except json.JSONDecodeError:
        st.error("❌ Error parsing glossary.json.")
        return {}

# ---------------------------
# Highlight glossary terms
# ---------------------------
def highlight_terms(text, glossary):
    """
    Highlights glossary terms in the given text with tooltips.
    Each term appears bold, colored, and shows its meaning on hover.
    """
    if not glossary or not text:
        return text

    # Sort terms by length (longest first to avoid partial overlaps)
    sorted_terms = sorted(glossary.keys(), key=len, reverse=True)

    for term in sorted_terms:
        meaning = glossary[term]
        pattern = r"\b" + re.escape(term) + r"\b"
        replacement = (
            f"<span class='tooltip'><b>{term}</b>"
            f"<span class='tooltiptext'>{meaning}</span></span>"
        )
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    return text

# ---------------------------
# Custom CSS for highlighting
# ---------------------------
def inject_glossary_styles():
    """Injects tooltip and highlight styles for glossary terms."""
    st.markdown(
        """
        <style>
        .tooltip {
            position: relative;
            display: inline-block;
            color: #0056b3;
            font-weight: 700;
            cursor: help;
            border-bottom: 2px dashed #0056b3;
            padding-bottom: 1px;
        }
        .tooltip .tooltiptext {
            visibility: hidden;
            width: 250px;
            background-color: #333;
            color: #fff;
            text-align: left;
            border-radius: 6px;
            padding: 10px;
            position: absolute;
            z-index: 1;
            bottom: 125%;
            left: 50%;
            margin-left: -125px;
            opacity: 0;
            transition: opacity 0.3s;
            font-size: 14px;
        }
        .tooltip:hover .tooltiptext {
            visibility: visible;
            opacity: 1;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


