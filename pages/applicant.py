import streamlit as st
import os
from datetime import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="Applicant Portal", layout="centered")

# --- TITLE ---
st.title("👤 Applicant Portal - Upload Your Resume")
st.caption("Upload your resume securely for screening")

# --- SETUP ---
UPLOAD_DIR = "resumes"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- APPLICANT INFO FORM ---
st.markdown("### 🧾 Applicant Details")
col1, col2 = st.columns(2)
name = col1.text_input("Full Name *", placeholder="Enter your full name")
email = col2.text_input("Email Address", placeholder="Enter your email (optional)")

st.markdown("### 📤 Upload Your Resume")
st.info("Please upload your resume in **PDF** or **DOCX** format. (Max size: 5MB)")

resume_file = st.file_uploader("Choose your resume file", type=["pdf", "docx"], label_visibility="collapsed")

# --- SUBMIT BUTTON ---
if resume_file and name:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{name.replace(' ', '_')}_{timestamp}.pdf"

    save_path = os.path.join(UPLOAD_DIR, filename)
    with open(save_path, "wb") as f:
        f.write(resume_file.getbuffer())

    st.success(f"✅ {name}, your resume has been uploaded successfully!")
    st.balloons()
    st.markdown(
        f"""
        **File Name:** {filename}  
        **Upload Time:** {datetime.now().strftime("%d-%m-%Y %H:%M:%S")}  
        **Status:** Uploaded Successfully ✅
        """
    )

    st.info("Thank you for applying! The recruiter will review your resume soon.")
elif resume_file and not name:
    st.warning("⚠️ Please enter your full name before uploading.")
else:
    st.write("Once uploaded, your resume will be automatically added to the system for screening.")
