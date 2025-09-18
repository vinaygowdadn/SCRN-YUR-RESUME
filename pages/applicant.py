import streamlit as st
import os
from utils import extract_text

st.set_page_config(page_title="Applicant Upload", layout="centered")
st.title("📄 Applicant Portal — Upload Resume")

UPLOAD_FOLDER = "resumes"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

st.write("Please upload your resume (PDF / DOCX / TXT).")

uploaded = st.file_uploader("Upload resume", type=["pdf","docx","txt"])
applicant_name = st.text_input("Optional: Enter your name (to rename saved file)")

if uploaded:
    name = applicant_name.strip() or uploaded.name
    save_name = name if name.lower().endswith(tuple([".pdf",".docx",".txt"])) else f"{name}_{uploaded.name}"
    save_path = os.path.join(UPLOAD_FOLDER, save_name)
    with open(save_path, "wb") as f:
        f.write(uploaded.getbuffer())
    st.success(f"✅ Saved as: {save_path}")
    # optional: preview text
    txt = extract_text(save_path)
    if txt:
        if st.checkbox("Show extracted text (preview)"):
            st.text_area("Preview", txt, height=250)