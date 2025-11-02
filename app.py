# import re
# import streamlit as st
# from io import BytesIO

# # Try spaCy NER
# USE_SPACY = False
# try:
#     import spacy
#     try:
#         nlp = spacy.load("en_core_web_sm")
#         USE_SPACY = True
#     except Exception:
#         # attempt to load via shortcut name if available; keep fallback
#         try:
#             from spacy.cli import download as spacy_download
#             spacy_download("en_core_web_sm")
#             nlp = spacy.load("en_core_web_sm")
#             USE_SPACY = True
#         except Exception:
#             USE_SPACY = False
# except Exception:
#     USE_SPACY = False

# # Regex-based detectors
# RE_PATTERNS = {
#     "EMAIL": r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
#     "SSN": r"\b\d{3}-\d{2}-\d{4}\b|\b\d{9}\b",
#     "PHONE": r"\b(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{2,4}\)?[-.\s]?)?\d{3,4}[-.\s]?\d{3,4}\b",
#     "DATE_ISO": r"\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b",
#     "DATE_TEXT": r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)\.? \d{1,2},? ?\d{0,4}\b",
#     "MRN": r"\bMRN[:#]?\s*\d{4,12}\b|\bMedicalRecordNumber[:#]?\s*\d{4,12}\b",
#     "CREDIT_CARD": r"\b(?:\d[ -]*?){13,16}\b",
#     "IP": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
#     "ADDRESS_SIMPLE": r"\b\d{1,5}\s+(?:[A-Za-z0-9]+\s){0,4}(?:Street|St|Avenue|Ave|Boulevard|Blvd|Road|Rd|Lane|Ln|Drive|Dr)\b",
# }

# # Combine regex into compiled patterns
# COMPILED = {k: re.compile(v) for k, v in RE_PATTERNS.items()}

# def regex_find_all(text):
#     """Return list of (label, start, end, matched_text) using regex detectors."""
#     matches = []
#     for label, pat in COMPILED.items():
#         for m in pat.finditer(text):
#             matches.append((label, m.start(), m.end(), m.group(0)))
#     # sort by start position
#     matches.sort(key=lambda x: x[1])
#     return matches

# def spacy_entities(text):
#     """Return list of (label, start, end, text) from spaCy if available."""
#     ents = []
#     if not USE_SPACY:
#         return ents
#     try:
#         doc = nlp(text)
#         for e in doc.ents:
#             # map spaCy labels to PHI-like labels
#             if e.label_ in ("PERSON", "DATE", "GPE", "LOC", "ORG"):
#                 ents.append((e.label_, e.start_char, e.end_char, e.text))
#     except Exception:
#         pass
#     return ents

# def merge_entities(regex_matches, spacy_matches):
#     """Merge two lists of matches, avoiding duplicates and overlapping by preferring longer spans."""
#     all_m = regex_matches + spacy_matches
#     # normalize labels from spaCy (PERSON -> NAME, DATE -> DATE, GPE/LOC -> ADDRESS)
#     normalized = []
#     for label, s, e, txt in all_m:
#         lab = label
#         if label == "PERSON":
#             lab = "NAME"
#         elif label == "GPE" or label == "LOC":
#             lab = "LOCATION"
#         elif label == "ORG":
#             lab = "ORG"
#         elif label == "DATE" or label == "DATE_ISO" or label == "DATE_TEXT":
#             lab = "DATE"
#         normalized.append((lab, s, e, txt))
#     # remove overlaps: choose match with larger span when overlapping
#     normalized.sort(key=lambda x: (x[1], -(x[2]-x[1])))  # by start, longer first
#     final = []
#     occupied = [False] * (len(max([txt for _,_,_,txt in normalized], default="")) + 1)  # dummy
#     # simpler approach: iterate and skip overlaps by indices
#     for item in normalized:
#         lab, s, e, txt = item
#         overlap = False
#         for _, s2, e2, _ in final:
#             if not (e <= s2 or s >= e2):
#                 overlap = True
#                 break
#         if not overlap:
#             final.append(item)
#     final.sort(key=lambda x: x[1])
#     return final

# def redact_text(text, placeholder="[REDACTED]"):
#     """Perform detection and redaction, returning sanitized text and the list of detected items."""
#     regex_matches = regex_find_all(text)
#     spacy_matches = spacy_entities(text)
#     merged = merge_entities(regex_matches, spacy_matches)
#     # Build redacted string
#     redacted = []
#     last = 0
#     detections = []
#     for lab, s, e, txt in merged:
#         detections.append({"label": lab, "text": txt, "start": s, "end": e})
#         redacted.append(text[last:s])
#         redacted.append(placeholder)
#         last = e
#     redacted.append(text[last:])
#     return "".join(redacted), detections

# # Streamlit UI
# st.set_page_config(page_title="Medical Data Privacy Guard", layout="wide")

# st.title("Medical Data Privacy Guard — Streamlit Demo")
# st.markdown("Upload or paste medical text")

# col1, col2 = st.columns([1,1])

# with col1:
#     st.header("Input")
#     text_input = st.text_area("Write here", height=300)
#     uploaded = st.file_uploader("Or upload a .txt file", type=["txt"])
#     if uploaded and not text_input:
#         try:
#             text_input = uploaded.read().decode("utf-8")
#         except Exception:
#             st.error("Unable to read file. Please ensure it's a UTF-8 text file.")

#     placeholder = st.text_input("Redaction placeholder", value="[REDACTED]")

#     if st.button("Sanitize / Redact"):
#         if not text_input or text_input.strip() == "":
#             st.warning("Please provide input text or upload a file.")
#         else:
#             redacted, detections = redact_text(text_input, placeholder=placeholder)
#             st.session_state["last_original"] = text_input
#             st.session_state["last_redacted"] = redacted
#             st.session_state["last_detections"] = detections
#             st.success(f"Sanitization complete — {len(detections)} items detected.")

# with col2:
#     st.header("Output")
#     if "last_redacted" in st.session_state:
#         st.subheader("Sanitized Text")
#         st.text_area("Sanitized output", value=st.session_state["last_redacted"], height=300)
#         st.subheader("Detected Entities / Matches")
#         dets = st.session_state.get("last_detections", [])
#         if dets:
#             for i, d in enumerate(dets, 1):
#                 st.write(f"{i}. **{d['label']}** — \"{d['text']}\" (chars {d['start']}–{d['end']})")
#         else:
#             st.write("No PHI detected by current detectors.")

#         # Download sanitized file
#         def get_bytes_io(content: str):
#             b = BytesIO()
#             b.write(content.encode("utf-8"))
#             b.seek(0)
#             return b

#         st.download_button("Download sanitized text (.txt)", data=get_bytes_io(st.session_state["last_redacted"]), file_name="sanitized.txt", mime="text/plain")
#     else:
#         st.info("Sanitized output will appear here after you press 'Sanitize / Redact'.")

# st.markdown("---")
# st.markdown("**Made by:** Abrar Hussain and Lingaraj")
# st.caption(f"spaCy available: {USE_SPACY}")


# import re
# import streamlit as st
# from io import BytesIO
# USE_SPACY = False
# try:
#     import spacy
#     try:
#         nlp = spacy.load("en_core_web_sm")
#         USE_SPACY = True
#     except Exception:
#         try:
#             from spacy.cli import download as spacy_download
#             spacy_download("en_core_web_sm")
#             nlp = spacy.load("en_core_web_sm")
#             USE_SPACY = True
#         except Exception:
#             USE_SPACY = False
# except Exception:
#     USE_SPACY = False

# RE_PATTERNS = {
#     "EMAIL": r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
#     "PHONE": r"\b(\+91[-\s]?)?[6-9]\d{9}\b",  # Indian phone numbers (start 6-9)
#     "DATE": r"\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b|\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b",
#     "ADDRESS_SIMPLE": r"\b\d{1,4}[A-Za-z]?\s+(?:[A-Za-z0-9]+\s){0,5}(?:Street|St|Road|Rd|Nagar|Layout|Colony|Lane|Avenue|Ave)[,]?(?:\s+[A-Za-z]+)?",
#     "AADHAAR": r"\b\d{4}\s\d{4}\s\d{4}\b",
#     "PAN": r"\b[A-Z]{5}\d{4}[A-Z]\b",
#     "PASSPORT": r"\b[A-Z][0-9]{7}\b",
#     "VOTER_ID": r"\b[A-Z]{3}\d{7}\b",
#     "DRIVING_LICENSE": r"\b[A-Z]{2}\d{2}\s?\d{11}\b",
#     "IP": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
#     "CREDIT_CARD": r"\b(?:\d[ -]*?){13,16}\b",
# }

# COMPILED = {k: re.compile(v) for k, v in RE_PATTERNS.items()}


# def regex_find_all(text, selected_labels):
#     matches = []
#     for label, pat in COMPILED.items():
#         if label not in selected_labels:
#             continue
#         for m in pat.finditer(text):
#             matches.append((label, m.start(), m.end(), m.group(0)))
#     matches.sort(key=lambda x: x[1])
#     return matches


# def spacy_entities(text, selected_labels):
#     ents = []
#     if not USE_SPACY or "NAME" not in selected_labels:
#         return ents
#     try:
#         doc = nlp(text)
#         for e in doc.ents:
#             if e.label_ == "PERSON":
#                 ents.append(("NAME", e.start_char, e.end_char, e.text))
#     except Exception:
#         pass
#     return ents


# def merge_entities(regex_matches, spacy_matches):
#     all_m = regex_matches + spacy_matches
#     all_m.sort(key=lambda x: (x[1], -(x[2] - x[1])))
#     final = []
#     for item in all_m:
#         overlap = False
#         for _, s2, e2, _ in final:
#             if not (item[2] <= s2 or item[1] >= e2):
#                 overlap = True
#                 break
#         if not overlap:
#             final.append(item)
#     final.sort(key=lambda x: x[1])
#     return final


# def redact_text(text, selected_labels, placeholder="[REDACTED]"):
#     regex_matches = regex_find_all(text, selected_labels)
#     spacy_matches = spacy_entities(text, selected_labels)
#     merged = merge_entities(regex_matches, spacy_matches)

#     redacted = []
#     last = 0
#     detections = []
#     for lab, s, e, txt in merged:
#         detections.append({"label": lab, "text": txt, "start": s, "end": e})
#         redacted.append(text[last:s])
#         redacted.append(placeholder)
#         last = e
#     redacted.append(text[last:])
#     return "".join(redacted), detections


# st.set_page_config(page_title="Medical Data Privacy Guard — India Edition", layout="wide")
# st.title("🇮🇳 Medical Data Privacy Guard (India Edition)")
# st.markdown("Upload or paste text and choose which personal data types you want to redact.")

# st.sidebar.header("Select Data Types to Redact")
# options = list(RE_PATTERNS.keys()) + ["NAME"]
# selected = st.sidebar.multiselect(
#     "Choose which categories to hide:",
#     options,
#     default=["NAME", "PHONE", "EMAIL", "AADHAAR", "PAN", "ADDRESS_SIMPLE"],
# )

# st.sidebar.write("✅ Selected for redaction:", ", ".join(selected) if selected else "None")

# col1, col2 = st.columns([1, 1])

# with col1:
#     st.header("Input")
#     text_input = st.text_area("Write or paste your text below:", height=300)
#     uploaded = st.file_uploader("Or upload a .txt file", type=["txt"])
#     if uploaded and not text_input:
#         try:
#             text_input = uploaded.read().decode("utf-8")
#         except Exception:
#             st.error("Unable to read file. Please ensure it's a UTF-8 text file.")

#     placeholder = st.text_input("Redaction placeholder", value="[REDACTED]")

#     if st.button("Sanitize / Redact"):
#         if not text_input or text_input.strip() == "":
#             st.warning("Please provide input text or upload a file.")
#         elif not selected:
#             st.warning("Please select at least one category to redact.")
#         else:
#             redacted, detections = redact_text(text_input, selected, placeholder)
#             st.session_state["last_original"] = text_input
#             st.session_state["last_redacted"] = redacted
#             st.session_state["last_detections"] = detections
#             st.session_state["last_selected"] = selected
#             st.success(f"Sanitization complete — {len(detections)} items detected.")


# with col2:
#     st.header("Output")
#     if "last_redacted" in st.session_state:
#         st.subheader("Sanitized Text")
#         st.text_area("Output:", value=st.session_state["last_redacted"], height=300)
#         st.subheader("Detected Entities / Matches")

#         dets = st.session_state.get("last_detections", [])
#         if dets:
#             for i, d in enumerate(dets, 1):
#                 st.write(f"{i}. **{d['label']}** — “{d['text']}” (chars {d['start']}–{d['end']})")
#         else:
#             st.write("No matches detected for selected categories.")

#         def get_bytes_io(content: str):
#             b = BytesIO()
#             b.write(content.encode("utf-8"))
#             b.seek(0)
#             return b

#         st.download_button(
#             "Download sanitized text (.txt)",
#             data=get_bytes_io(st.session_state["last_redacted"]),
#             file_name="sanitized.txt",
#             mime="text/plain",
#         )
#     else:
#         st.info("Sanitized output will appear here after you press 'Sanitize / Redact'.")


# st.markdown("---")
# st.markdown("**Made by:** Abrar Hussain and Lingaraj")
# st.caption(f"spaCy available: {USE_SPACY}")



import re
import streamlit as st
from io import BytesIO

USE_SPACY = False
try:
    import spacy
    try:
        nlp = spacy.load("en_core_web_sm")
        USE_SPACY = True
    except Exception:
        try:
            from spacy.cli import download as spacy_download
            spacy_download("en_core_web_sm")
            nlp = spacy.load("en_core_web_sm")
            USE_SPACY = True
        except Exception:
            USE_SPACY = False
except Exception:
    USE_SPACY = False

RE_PATTERNS = {
    "EMAIL": r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
    "PHONE": r"\b(\+91[-\s]?)?[6-9]\d{9}\b",
    "DATE": r"\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b|\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b",
    "ADDRESS_SIMPLE": r"\b\d{1,4}[A-Za-z]?\s+(?:[A-Za-z0-9]+\s){0,5}(?:Street|St|Road|Rd|Nagar|Layout|Colony|Lane|Avenue|Ave)[,]?(?:\s+[A-Za-z]+)?",
    "AADHAAR": r"\b\d{4}\s\d{4}\s\d{4}\b",
    "PAN": r"\b[A-Z]{5}\d{4}[A-Z]\b",
    "PASSPORT": r"\b[A-Z][0-9]{7}\b",
    "VOTER_ID": r"\b[A-Z]{3}\d{7}\b",
    "DRIVING_LICENSE": r"\b[A-Z]{2}\d{2}\s?\d{11}\b",
    "IP": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
    "CREDIT_CARD": r"\b(?:\d[ -]*?){13,16}\b",
}

COMPILED = {k: re.compile(v) for k, v in RE_PATTERNS.items()}

def regex_find_all(text, selected_labels):
    matches = []
    for label, pat in COMPILED.items():
        if label not in selected_labels:
            continue
        for m in pat.finditer(text):
            matches.append((label, m.start(), m.end(), m.group(0)))
    matches.sort(key=lambda x: x[1])
    return matches

def spacy_entities(text, selected_labels):
    ents = []
    if not USE_SPACY or "NAME" not in selected_labels:
        return ents
    try:
        doc = nlp(text)
        for e in doc.ents:
            if e.label_ == "PERSON":
                ents.append(("NAME", e.start_char, e.end_char, e.text))
    except Exception:
        pass
    return ents

def merge_entities(regex_matches, spacy_matches):
    all_m = regex_matches + spacy_matches
    all_m.sort(key=lambda x: (x[1], -(x[2] - x[1])))
    final = []
    for item in all_m:
        overlap = False
        for _, s2, e2, _ in final:
            if not (item[2] <= s2 or item[1] >= e2):
                overlap = True
                break
        if not overlap:
            final.append(item)
    final.sort(key=lambda x: x[1])
    return final

def redact_text(text, selected_labels, placeholder="[REDACTED]"):
    regex_matches = regex_find_all(text, selected_labels)
    spacy_matches = spacy_entities(text, selected_labels)
    merged = merge_entities(regex_matches, spacy_matches)
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

st.set_page_config(page_title="Medical Data Privacy Guard", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif !important;
    }
    
    #MainMenu, footer, header, .stDeployButton {visibility: hidden; display: none;}
    
    .stApp {
        background: #0a0e1a;
        overflow: hidden;
    }
    
    .main .block-container {
        padding: 1.5rem 2rem !important;
        max-width: 100% !important;
        max-height: 100vh !important;
        overflow: hidden !important;
    }
    
    /* HEADER */
    .premium-header {
        background: linear-gradient(135deg, #1a1f35 0%, #242b42 100%);
        border: 1px solid #2d3548;
        border-radius: 12px;
        padding: 1.2rem 1.8rem;
        margin-bottom: 1.2rem;
        display: flex;
        align-items: center;
        gap: 1rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.4);
    }
    
    .premium-header h1 {
        color: #ffffff;
        font-size: 1.5rem;
        font-weight: 700;
        margin: 0;
        line-height: 1.2;
    }
    
    .premium-header p {
        color: #8b92a8;
        font-size: 0.8rem;
        margin: 0.3rem 0 0 0;
        line-height: 1.3;
    }
    
    /* MAIN GRID */
    [data-testid="column"] {
        background: #151925;
        border: 1px solid #252b3d;
        border-radius: 12px;
        padding: 1.2rem !important;
        height: calc(100vh - 200px) !important;
        overflow-y: auto;
        box-shadow: 0 2px 12px rgba(0,0,0,0.3);
    }
    
    [data-testid="column"]::-webkit-scrollbar {
        width: 6px;
    }
    
    [data-testid="column"]::-webkit-scrollbar-track {
        background: #1a1f2e;
        border-radius: 3px;
    }
    
    [data-testid="column"]::-webkit-scrollbar-thumb {
        background: #2d3548;
        border-radius: 3px;
    }
    
    /* SECTION HEADERS */
    .section-header {
        color: #ffffff;
        font-size: 0.95rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 1rem;
        padding-bottom: 0.7rem;
        border-bottom: 2px solid #2d3548;
    }
    
    /* MULTISELECT */
    .stMultiSelect [data-baseweb="select"] {
        background: #0d1117 !important;
        border: 1px solid #2d3548 !important;
        border-radius: 8px !important;
    }
    
    .stMultiSelect [data-baseweb="tag"] {
        background: #1e3a5f !important;
        border: 1px solid #2563eb !important;
        color: #60a5fa !important;
        border-radius: 6px !important;
        padding: 0.25rem 0.6rem !important;
        font-size: 0.75rem !important;
        font-weight: 600 !important;
        margin: 0.15rem !important;
    }
    
    .stMultiSelect [data-baseweb="tag"] svg {
        fill: #60a5fa !important;
    }
    
    .stMultiSelect input {
        color: #ffffff !important;
    }
    
    /* TEXT AREAS */
    .stTextArea textarea {
        background: #0d1117 !important;
        border: 1px solid #2d3548 !important;
        border-radius: 8px !important;
        color: #ffffff !important;
        font-size: 0.85rem !important;
        padding: 0.8rem !important;
        height: 140px !important;
        resize: none !important;
        line-height: 1.5 !important;
    }
    
    .stTextArea textarea::placeholder {
        color: #4a5568 !important;
    }
    
    .stTextArea textarea:focus {
        border-color: #2563eb !important;
        box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.1) !important;
        outline: none !important;
    }
    
    /* TEXT INPUT */
    .stTextInput input {
        background: #0d1117 !important;
        border: 1px solid #2d3548 !important;
        border-radius: 8px !important;
        color: #ffffff !important;
        padding: 0.6rem 0.8rem !important;
        font-size: 0.85rem !important;
    }
    
    .stTextInput input:focus {
        border-color: #2563eb !important;
        box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.1) !important;
        outline: none !important;
    }
    
    /* FILE UPLOADER */
    .stFileUploader {
        background: #0d1117 !important;
        border: 1px dashed #2d3548 !important;
        border-radius: 8px !important;
        padding: 0.8rem !important;
    }
    
    .stFileUploader section {
        border: none !important;
        padding: 0.5rem !important;
    }
    
    .stFileUploader button {
        background: #1e293b !important;
        color: #ffffff !important;
        border: 1px solid #2d3548 !important;
        border-radius: 6px !important;
        padding: 0.5rem 1rem !important;
        font-size: 0.8rem !important;
    }
    
    /* MAIN BUTTON */
    .stButton button {
        background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.8rem 1.5rem !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        width: 100% !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3) !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }
    
    .stButton button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(37, 99, 235, 0.4) !important;
        background: linear-gradient(135deg, #1d4ed8 0%, #6d28d9 100%) !important;
    }
    
    .stButton button:active {
        transform: translateY(0) !important;
    }
    
    /* DOWNLOAD BUTTON */
    .stDownloadButton button {
        background: #1e293b !important;
        color: #60a5fa !important;
        border: 1px solid #2563eb !important;
        border-radius: 8px !important;
        padding: 0.6rem 1.2rem !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
        width: 100% !important;
        transition: all 0.2s ease !important;
    }
    
    .stDownloadButton button:hover {
        background: #2563eb !important;
        color: #ffffff !important;
    }
    
    /* ALERTS */
    .stSuccess {
        background: #1a2e1a !important;
        border: 1px solid #22c55e !important;
        border-radius: 8px !important;
        color: #4ade80 !important;
        padding: 0.7rem 1rem !important;
        font-size: 0.85rem !important;
    }
    
    .stWarning {
        background: #2e2a1a !important;
        border: 1px solid #f59e0b !important;
        border-radius: 8px !important;
        color: #fbbf24 !important;
        padding: 0.7rem 1rem !important;
        font-size: 0.85rem !important;
    }
    
    .stInfo {
        background: #1a1f2e !important;
        border: 1px solid #2563eb !important;
        border-radius: 8px !important;
        color: #60a5fa !important;
        padding: 0.7rem 1rem !important;
        font-size: 0.85rem !important;
    }
    
    /* LABELS */
    label {
        color: #8b92a8 !important;
        font-weight: 500 !important;
        font-size: 0.8rem !important;
        margin-bottom: 0.4rem !important;
    }
    
    /* STATUS TEXT */
    .status-text {
        color: #4ade80;
        font-size: 0.75rem;
        font-weight: 600;
        margin-top: 0.5rem;
        padding: 0.4rem 0.7rem;
        background: #1a2e1a;
        border: 1px solid #22c55e;
        border-radius: 6px;
        display: inline-block;
    }
    
    /* DETECTION ITEMS */
    .detection-box {
        background: #0d1117;
        border: 1px solid #2d3548;
        border-radius: 6px;
        padding: 0.6rem 0.8rem;
        margin: 0.4rem 0;
        font-size: 0.8rem;
        display: flex;
        align-items: center;
        gap: 0.7rem;
    }
    
    .detection-badge {
        background: #1e3a5f;
        color: #60a5fa;
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        font-weight: 700;
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.3px;
        flex-shrink: 0;
    }
    
    .detection-content {
        color: #d1d5db;
        font-family: 'Courier New', monospace;
        flex: 1;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    
    .detection-pos {
        color: #6b7280;
        font-size: 0.7rem;
        flex-shrink: 0;
    }
    
    /* FOOTER */
    .premium-footer {
        text-align: center;
        color: #4a5568;
        font-size: 0.75rem;
        margin-top: 1rem;
        padding-top: 0.8rem;
        border-top: 1px solid #252b3d;
    }
    
    .premium-footer strong {
        color: #8b92a8;
    }
    
    /* HIDE STREAMLIT BRANDING */
    .css-1dp5vir {
        display: none;
    }
    
    /* RESPONSIVE */
    @media (max-height: 900px) {
        [data-testid="column"] {
            height: calc(100vh - 180px) !important;
        }
        .stTextArea textarea {
            height: 120px !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="premium-header">
    <div>
        <h1>🛡️ Medical Data Privacy Guard</h1>
        <p>India Edition • Secure your sensitive medical data with advanced redaction</p>
    </div>
</div>
""", unsafe_allow_html=True)

# Three column layout - proper proportions
col1, col2, col3 = st.columns([2.5, 3.5, 4])

with col1:
    st.markdown('<div class="section-header">DATA TYPES</div>', unsafe_allow_html=True)
    
    options = list(RE_PATTERNS.keys()) + ["NAME"]
    selected = st.multiselect(
        "Select categories:",
        options,
        default=["NAME", "PHONE", "EMAIL", "AADHAAR", "PAN", "ADDRESS_SIMPLE"],
        label_visibility="collapsed"
    )
    
    if selected:
        st.markdown(f'<div class="status-text">✓ {len(selected)} selected</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="section-header">INPUT</div>', unsafe_allow_html=True)
    
    text_input = st.text_area(
        "text",
        height=140,
        label_visibility="collapsed",
        placeholder="Paste your medical text here..."
    )
    
    uploaded = st.file_uploader("Upload .txt file", type=["txt"], label_visibility="collapsed")
    if uploaded and not text_input:
        try:
            text_input = uploaded.read().decode("utf-8")
            st.success("✓ File loaded")
        except Exception:
            st.error("Failed to read file")

    placeholder = st.text_input("Placeholder:", value="[REDACTED]")

    if st.button("🔒 SANITIZE / REDACT"):
        if not text_input or text_input.strip() == "":
            st.warning("⚠ Please provide text")
        elif not selected:
            st.warning("⚠ Select at least one category")
        else:
            redacted, detections = redact_text(text_input, selected, placeholder)
            st.session_state["last_redacted"] = redacted
            st.session_state["last_detections"] = detections
            st.success(f"✓ Complete — {len(detections)} items detected")

with col3:
    st.markdown('<div class="section-header">OUTPUT</div>', unsafe_allow_html=True)
    
    if "last_redacted" in st.session_state:
        st.text_area(
            "output",
            value=st.session_state["last_redacted"],
            height=140,
            label_visibility="collapsed"
        )
        
        def get_bytes_io(content: str):
            b = BytesIO()
            b.write(content.encode("utf-8"))
            b.seek(0)
            return b

        st.download_button(
            "⬇ DOWNLOAD",
            data=get_bytes_io(st.session_state["last_redacted"]),
            file_name="sanitized.txt",
            mime="text/plain",
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("**Detected Entities:**")
        
        dets = st.session_state.get("last_detections", [])
        if dets:
            for d in dets:
                st.markdown(f"""
                <div class="detection-box">
                    <span class="detection-badge">{d['label']}</span>
                    <span class="detection-content">"{d['text']}"</span>
                    <span class="detection-pos">{d['start']}-{d['end']}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No matches found")
    else:
        st.info("Output will appear here after processing")

st.markdown(f"""
<div class="premium-footer">
    Made by <strong>Abrar Hussain</strong> and <strong>Lingaraj</strong> • spaCy: {USE_SPACY}
</div>
""", unsafe_allow_html=True)