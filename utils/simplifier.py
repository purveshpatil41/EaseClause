# simplifier.py
import re
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize

# ---------------------------
# NLTK setup
# ---------------------------
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
STOPWORDS = set(stopwords.words('english'))

# ---------------------------
# Common replacements
# ---------------------------
COMMON_REPLACEMENTS = {
    "utilize": "use",
    "commence": "start",
    "terminate": "end",
    "endeavor": "try",
    "assistance": "help",
    "individuals": "people",
    "approximately": "about",
    "purchase": "buy",
    "objective": "goal",
    "requirement": "need",
    "consequently": "so",
    "therefore": "so",
    "subsequently": "after",
    "nevertheless": "but",
    "furthermore": "also",
    "in addition": "also",
    "in order to": "to",
    "in the event that": "if",
    "in accordance with": "under",
    "hereinafter": "from now on",
    "aforementioned": "mentioned earlier",
    "pursuant to": "under",
    "in witness whereof": "to confirm this",
}

# ---------------------------
# T5 Model
# ---------------------------
MODEL_NAME = "t5-small"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)

# ---------------------------
# Utility functions
# ---------------------------
def clean_and_join(sentences):
    sentences = [s.strip().capitalize() for s in sentences if s.strip()]
    return ". ".join(sentences).strip()

def apply_replacements(text, replacements):
    for key, val in replacements.items():
        text = re.sub(rf"\b{key}\b", val, text, flags=re.IGNORECASE)
    return text

# ---------------------------
# Level-specific simplifiers
# ---------------------------
def basic_simplify(text: str) -> str:
    """Removes common stopwords to make text more direct."""
    sentences = sent_tokenize(text)
    simplified = []
    for s in sentences:
        words = word_tokenize(s)
        filtered = [w for w in words if w.lower() not in STOPWORDS]
        simplified.append(" ".join(filtered))
    return clean_and_join(simplified)

def intermediate_simplify(text: str) -> str:
    """Replaces complex words with common synonyms."""
    return apply_replacements(text, COMMON_REPLACEMENTS)

def advanced_simplify(text: str) -> str:
    """Applies multiple layers of replacements and sentence compression."""
    text = intermediate_simplify(text)
    
    deep_replacements = {
        r"\bthe party of the first part\b": "first person",
        r"\bthe party of the second part\b": "second person",
        r"\bshall\b": "will",
        r"\bmust\b": "has to",
        r"\bprior to\b": "before",
        r"\bat this point in time\b": "now",
    }
    text = apply_replacements(text, deep_replacements)

    sentences = sent_tokenize(text)
    compressed = []
    for s in sentences:
        if len(s.split()) > 20:
            s = " ".join(s.split()[:15]) + "..."
        compressed.append(s)
    return clean_and_join(compressed)

# ---------------------------
# T5 simplification (optional, better readability)
# ---------------------------
PREFIXES = {
    "Basic": "Simplify for a beginner reader: ",
    "Intermediate": "Simplify and clarify: ",
    "Advanced": "Simplify, compress and shorten: "
}

def simplify_text(text: str, level: str) -> str:
    if not text.strip():
        return "Please enter text to simplify."

    # Step 1: Rule-based simplification
    if level == "Basic":
        rule_text = basic_simplify(text)
    elif level == "Intermediate":
        rule_text = intermediate_simplify(text)
    elif level == "Advanced":
        rule_text = advanced_simplify(text)
    else:
        rule_text = text

    # Step 2: T5 model
    prefix = PREFIXES.get(level, "")
    input_text = prefix + rule_text
    inputs = tokenizer(input_text, return_tensors="pt", max_length=512, truncation=True)
    
    if level == "Advanced":
        outputs = model.generate(**inputs, max_length=150, num_beams=5, early_stopping=True)
    else:
        outputs = model.generate(**inputs, max_length=512, num_beams=4)
        
    simplified = tokenizer.decode(outputs[0], skip_special_tokens=True)

    return simplified



