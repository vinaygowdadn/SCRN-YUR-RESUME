import streamlit as st
import os
import pandas as pd
from utils import (
    extract_text,
    extract_keywords,
    generate_wordcloud,
    compute_similarity,
    extract_snippets,
    df_to_csv_bytes,
    df_to_pdf_bytes
)

# --- PAGE CONFIG ---
st.set_page_config(page_title="Recruiter Dashboard", layout="wide")

# --- TITLE ---
st.title("👔 Recruiter Dashboard - AI Resume Screening Tool")
st.caption("Automate your resume shortlisting using AI and NLP")

# --- PASSWORD LOGIN ---
RECRUITER_PASSWORD = "admin123"
password = st.text_input("🔒 Enter Recruiter Password", type="password")

if password != RECRUITER_PASSWORD:
    st.warning("Please enter the correct password to continue.")
    st.stop()

st.success("✅ Logged in successfully as Recruiter!")

# --- JOB DESCRIPTION UPLOAD ---
st.subheader("📄 Upload Job Description(s)")
jd_files = st.file_uploader(
    "Upload one or more JD files (PDF or DOCX)",
    type=["pdf", "docx"],
    accept_multiple_files=True
)

# --- FOLDER SETUP ---
RESUME_DIR = "resumes"
JD_DIR = "job_descriptions"
os.makedirs(RESUME_DIR, exist_ok=True)
os.makedirs(JD_DIR, exist_ok=True)

# --- PROCESS EACH JOB DESCRIPTION ---
if jd_files:
    for jd_file in jd_files:
        st.markdown("---")
        st.header(f"🧾 Job Description: {jd_file.name}")

        # Save JD to job_descriptions folder
        jd_save_path = os.path.join(JD_DIR, jd_file.name)
        with open(jd_save_path, "wb") as f:
            f.write(jd_file.getbuffer())
        st.success(f"📂 JD saved to folder: `{jd_save_path}`")

        # Extract JD text for processing
        jd_text = extract_text(jd_file)

        if not jd_text.strip():
            st.error("⚠️ Could not extract text from this JD. Try a different file.")
            continue

        # --- WORD CLOUD ---
        with st.expander("📊 View JD Word Cloud", expanded=True):
            st.pyplot(generate_wordcloud(jd_text))

        # --- LOAD RESUMES ---
        resumes = []
        for fname in os.listdir(RESUME_DIR):
            if fname.lower().endswith((".pdf", ".docx")):
                path = os.path.join(RESUME_DIR, fname)
                with open(path, "rb") as file:
                    text = extract_text(file)
                resumes.append({"filename": fname, "text": text})

        if not resumes:
            st.warning("⚠️ No resumes found in the 'resumes/' folder. Ask applicants to upload theirs.")
            continue

        # --- CALCULATE SIMILARITY ---
        scores, vectorizer = compute_similarity(jd_text, resumes)
        jd_keywords = extract_keywords(jd_text, top_n=20)

        results = []
        for resume, score in zip(resumes, scores):
            snippets = extract_snippets(resume["text"], jd_keywords)
            results.append({
                "Resume": resume["filename"],
                "Match %": round(score * 100, 2),
                "Matching Keywords": ", ".join(
                    [k for k in jd_keywords if k.lower() in resume["text"].lower()]
                ),
                "Snippet": " | ".join(snippets)
            })

        df = pd.DataFrame(results).sort_values(by="Match %", ascending=False)

        # --- SHOW RESULTS ---
        st.subheader("📊 Matching Results (Ranked by Similarity)")

        for _, row in df.iterrows():
            match_score = row["Match %"]
            progress_color = "green" if match_score >= 70 else "orange" if match_score >= 40 else "red"

            st.markdown(f"### 🧍 {row['Resume']}")
            st.progress(match_score / 100)
            st.markdown(f"**Match Percentage:** <span style='color:{progress_color}; font-weight:bold;'>{match_score}%</span>", unsafe_allow_html=True)

            if row["Matching Keywords"]:
                st.markdown(f"**Matched Keywords:** `{row['Matching Keywords']}`")

            if row["Snippet"]:
                st.info(f"📄 Snippet: {row['Snippet'][:300]}...")

            st.markdown("---")

        # --- DOWNLOAD REPORTS ---
        st.subheader("⬇️ Download Reports")
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                "📥 Download CSV Report",
                df_to_csv_bytes(df),
                file_name=f"{jd_file.name}_results.csv",
                mime="text/csv"
            )
        with col2:
            pdf_buf = df_to_pdf_bytes(df, title=f"Matching Report - {jd_file.name}")
            st.download_button(
                "📄 Download PDF Report",
                pdf_buf,
                file_name=f"{jd_file.name}_results.pdf",
                mime="application/pdf"
            )
