import streamlit as st

st.set_page_config(page_title="Resume Screening Tool", layout="centered")

st.title("🏆 AI-Powered Resume Screening Tool")
st.write("Choose your role to proceed:")

if st.button("📄 Applicant - Upload Resume"):
    st.switch_page("pages/applicant.py")

if st.button("👔 Recruiter - Dashboard"):
    st.switch_page("pages/recruiter.py")