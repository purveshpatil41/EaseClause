import streamlit as st
from backend_module import simplify_text, summarize_text

st.set_page_config(
    page_title="Contract Simplifier & Summarizer",
    layout="wide",
    initial_sidebar_state="expanded"
)

# DARK MODE CSS (background + text colors)
dark_css = """
<style>
    /* Backgrounds */
    section.main {
        background-color: #0e1117 !important;
        color: #E0E0E0 !important;
    }
    div[data-testid="stSidebar"] > div:first-child {
        background-color: #0e1117 !important;
        color: #E0E0E0 !important;
    }

    /* Text colors */
    .css-18e3th9, .css-1d391kg, .css-1v0mbdj, .css-1r6slb0 {
        color: #E0E0E0 !important;
    }

    /* Links */
    a, a:hover, a:visited {
        color: #9CDCFE !important;
    }

    /* Buttons */
    button, .st-bq {
        background-color: #25282d !important;
        color: #E0E0E0 !important;
        border: none !important;
    }

    /* Text input backgrounds */
    .stTextInput > div > input, textarea {
        background-color: #25282d !important;
        color: #E0E0E0 !important;
    }
</style>
"""

# LIGHT MODE CSS (background + text colors)
light_css = """
<style>
    section.main {
        background-color: white !important;
        color: black !important;
    }
    div[data-testid="stSidebar"] > div:first-child {
        background-color: white !important;
        color: black !important;
    }

    .css-18e3th9, .css-1d391kg, .css-1v0mbdj, .css-1r6slb0 {
        color: black !important;
    }

    a, a:hover, a:visited {
        color: #1a0dab !important;
    }

    button, .st-bq {
        background-color: #f0f0f0 !important;
        color: black !important;
        border: none !important;
    }

    .stTextInput > div > input, textarea {
        background-color: white !important;
        color: black !important;
    }
</style>
"""

# Sidebar toggle
theme = st.sidebar.radio("🌗 Theme", ["Light", "Dark"])

if theme == "Dark":
    st.markdown(dark_css, unsafe_allow_html=True)
else:
    st.markdown(light_css, unsafe_allow_html=True)

st.title("📃 Contract Simplifier & Summarizer")

st.markdown("""
Use this tool to *Simplify* or *Summarize* lengthy contract/policy text.  
Paste the text or upload a .txt file, choose an action, and view results side by side.
""")

st.subheader("Step 1: Provide Input")
input_method = st.radio("Choose input method", ["Paste Text", "Upload .txt File"])

input_text = ""

if input_method == "Paste Text":
    input_text = st.text_area("Paste your text here:", height=300)
else:
    uploaded_file = st.file_uploader("Upload a .txt file", type=["txt"])
    if uploaded_file:
        input_text = uploaded_file.read().decode("utf-8")

if input_text.strip():
    word_count = len(input_text.strip().split())
    st.info(f"🧮 Word Count: {word_count}")

st.subheader("Step 2: Choose Operation")
task = st.radio("Select an action", ["Simplify", "Summarize"])

if st.button("Process"):
    if not input_text.strip():
        st.warning("⚠ Please provide some input text first.")
    else:
        with st.spinner("⏳ Processing..."):
            if task == "Simplify":
                output_text = simplify_text(input_text)
            else:
                output_text = summarize_text(input_text)

        st.subheader("📤 Results")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 📝 Original Text")
            st.write(input_text)

        with col2:
            st.markdown(f"### ✨ {task}d Text")
            st.write(output_text)

            st.download_button(
                label="📥 Download Result",
                data=output_text,
                file_name=f"{task.lower()}_output.txt",
                mime="text/plain"
            )

st.markdown("---")
st.markdown(
    "🔧 Built by *Team Milestone 3* | 💡 Use responsibly – this tool is for educational purposes."
)
