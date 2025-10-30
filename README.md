# Medical Data Privacy Guard (Streamlit Demo)

This repository is a cleaned and deploy-ready version of the "Medical Data Privacy Guard" project designed for Streamlit deployment. It focuses on detecting and redacting common PHI/PII patterns in free text using regex-based detectors and optional spaCy NER.

## Files
- `app.py` — Single-file Streamlit app (main).
- `requirements.txt` — Python dependencies (Streamlit and spaCy).
- `.streamlit/config.toml` — Streamlit default config for wide layout.


## How to run locally
1. Create a virtual environment and activate it.
2. `pip install -r requirements.txt`
3. (Optional but recommended) Install the spaCy small model:
   ```bash
   python -m spacy download en_core_web_sm
   ```
4. Run the app:
   ```bash
   streamlit run app.py
   ```

## How to deploy to Streamlit Cloud
1. Push this project to a GitHub repo.
2. On Streamlit Cloud, create a new app pointing to this repository.
3. Ensure `requirements.txt` is used by the platform.
4. If you included the spaCy model line in `requirements.txt` (commented sample is provided), the model will be installed automatically. Otherwise add `python -m spacy download en_core_web_sm` to an init script.

## Limitations & Next steps
- Regex detection has limitations and may miss context-sensitive PHI or produce false positives.
- For production-grade de-identification: consider using established libraries (Microsoft Presidio, Amazon Comprehend Medical, or more robust models) and secure deployment with audit logging and encryption.
- Add unit tests, enterprise logging (without storing raw PHI), and validation against labeled datasets (like MIMIC-derived synthetic examples).

This project was prepared as a working deliverable for the Team1 SRS for the Generative AI course project.
