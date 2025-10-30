import re
import streamlit as st
from io import BytesIO

# Try spaCy NER
USE_SPACY = False
try:
    import spacy
    try:
        nlp = spacy.load("en_core_web_sm")
        USE_SPACY = True
    except Exception:
        # attempt to load via shortcut name if available; keep fallback
        try:
            from spacy.cli import download as spacy_download
            spacy_download("en_core_web_sm")
            nlp = spacy.load("en_core_web_sm")
            USE_SPACY = True
        except Exception:
            USE_SPACY = False
except Exception:
    USE_SPACY = False

# Regex-based detectors
RE_PATTERNS = {
    "EMAIL": r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
    "SSN": r"\b\d{3}-\d{2}-\d{4}\b|\b\d{9}\b",
    "PHONE": r"\b(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{2,4}\)?[-.\s]?)?\d{3,4}[-.\s]?\d{3,4}\b",
    "DATE_ISO": r"\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b",
    "DATE_TEXT": r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)\.? \d{1,2},? ?\d{0,4}\b",
    "MRN": r"\bMRN[:#]?\s*\d{4,12}\b|\bMedicalRecordNumber[:#]?\s*\d{4,12}\b",
    "CREDIT_CARD": r"\b(?:\d[ -]*?){13,16}\b",
    "IP": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
    "ADDRESS_SIMPLE": r"\b\d{1,5}\s+(?:[A-Za-z0-9]+\s){0,4}(?:Street|St|Avenue|Ave|Boulevard|Blvd|Road|Rd|Lane|Ln|Drive|Dr)\b",
}

# Combine regex into compiled patterns
COMPILED = {k: re.compile(v) for k, v in RE_PATTERNS.items()}

def regex_find_all(text):
    """Return list of (label, start, end, matched_text) using regex detectors."""
    matches = []
    for label, pat in COMPILED.items():
        for m in pat.finditer(text):
            matches.append((label, m.start(), m.end(), m.group(0)))
    # sort by start position
    matches.sort(key=lambda x: x[1])
    return matches

def spacy_entities(text):
    """Return list of (label, start, end, text) from spaCy if available."""
    ents = []
    if not USE_SPACY:
        return ents
    try:
        doc = nlp(text)
        for e in doc.ents:
            # map spaCy labels to PHI-like labels
            if e.label_ in ("PERSON", "DATE", "GPE", "LOC", "ORG"):
                ents.append((e.label_, e.start_char, e.end_char, e.text))
    except Exception:
        pass
    return ents

def merge_entities(regex_matches, spacy_matches):
    """Merge two lists of matches, avoiding duplicates and overlapping by preferring longer spans."""
    all_m = regex_matches + spacy_matches
    # normalize labels from spaCy (PERSON -> NAME, DATE -> DATE, GPE/LOC -> ADDRESS)
    normalized = []
    for label, s, e, txt in all_m:
        lab = label
        if label == "PERSON":
            lab = "NAME"
        elif label == "GPE" or label == "LOC":
            lab = "LOCATION"
        elif label == "ORG":
            lab = "ORG"
        elif label == "DATE" or label == "DATE_ISO" or label == "DATE_TEXT":
            lab = "DATE"
        normalized.append((lab, s, e, txt))
    # remove overlaps: choose match with larger span when overlapping
    normalized.sort(key=lambda x: (x[1], -(x[2]-x[1])))  # by start, longer first
    final = []
    occupied = [False] * (len(max([txt for _,_,_,txt in normalized], default="")) + 1)  # dummy
    # simpler approach: iterate and skip overlaps by indices
    for item in normalized:
        lab, s, e, txt = item
        overlap = False
        for _, s2, e2, _ in final:
            if not (e <= s2 or s >= e2):
                overlap = True
                break
        if not overlap:
            final.append(item)
    final.sort(key=lambda x: x[1])
    return final

def redact_text(text, placeholder="[REDACTED]"):
    """Perform detection and redaction, returning sanitized text and the list of detected items."""
    regex_matches = regex_find_all(text)
    spacy_matches = spacy_entities(text)
    merged = merge_entities(regex_matches, spacy_matches)
    # Build redacted string
    redacted = []
    last = 0
    detections = []
    for lab, s, e, txt in merged:
        detections.append({"label": lab, "text": txt, "start": s, "end": e})
        redacted.append(text[last:s])
        redacted.append(placeholder)
        last = e
    redacted.append(text[last:])
    return "".join(redacted), detections

# Streamlit UI
st.set_page_config(page_title="Medical Data Privacy Guard", layout="wide")

st.title("Medical Data Privacy Guard — Streamlit Demo")
st.markdown("Upload or paste medical text")

col1, col2 = st.columns([1,1])

with col1:
    st.header("Input")
    text_input = st.text_area("Write here", height=300)
    uploaded = st.file_uploader("Or upload a .txt file", type=["txt"])
    if uploaded and not text_input:
        try:
            text_input = uploaded.read().decode("utf-8")
        except Exception:
            st.error("Unable to read file. Please ensure it's a UTF-8 text file.")

    placeholder = st.text_input("Redaction placeholder", value="[REDACTED]")

    if st.button("Sanitize / Redact"):
        if not text_input or text_input.strip() == "":
            st.warning("Please provide input text or upload a file.")
        else:
            redacted, detections = redact_text(text_input, placeholder=placeholder)
            st.session_state["last_original"] = text_input
            st.session_state["last_redacted"] = redacted
            st.session_state["last_detections"] = detections
            st.success(f"Sanitization complete — {len(detections)} items detected.")

with col2:
    st.header("Output")
    if "last_redacted" in st.session_state:
        st.subheader("Sanitized Text")
        st.text_area("Sanitized output", value=st.session_state["last_redacted"], height=300)
        st.subheader("Detected Entities / Matches")
        dets = st.session_state.get("last_detections", [])
        if dets:
            for i, d in enumerate(dets, 1):
                st.write(f"{i}. **{d['label']}** — \"{d['text']}\" (chars {d['start']}–{d['end']})")
        else:
            st.write("No PHI detected by current detectors.")

        # Download sanitized file
        def get_bytes_io(content: str):
            b = BytesIO()
            b.write(content.encode("utf-8"))
            b.seek(0)
            return b

        st.download_button("Download sanitized text (.txt)", data=get_bytes_io(st.session_state["last_redacted"]), file_name="sanitized.txt", mime="text/plain")
    else:
        st.info("Sanitized output will appear here after you press 'Sanitize / Redact'.")

st.markdown("---")
st.markdown("**Made by:** Abrar Hussain and Lingaraj")
st.caption(f"spaCy available: {USE_SPACY}")
