import streamlit as st
import os
import pandas as pd
from utils import extract_text, extract_keywords, generate_wordcloud_figure, compute_scores_for_resumes, extract_snippets, highlight_in_html, df_to_csv_bytes, df_to_pdf_bytes

st.set_page_config(page_title="Recruiter Dashboard", layout="wide")
st.title("👔 Recruiter Dashboard")

# ---------- Password (session-stored) ----------
RECRUITER_PASSWORD = "admin123"   # change before submission

if "recruiter_logged_in" not in st.session_state:
    st.session_state["recruiter_logged_in"] = False

if not st.session_state["recruiter_logged_in"]:
    pwd = st.text_input("Enter recruiter password", type="password")
    if st.button("Login"):
        if pwd == RECRUITER_PASSWORD:
            st.session_state["recruiter_logged_in"] = True
            st.rerun()
        else:
            st.error("Wrong password")
    st.stop()

st.success("✅ Logged in as recruiter")

# ---------- Upload multiple JD files ----------
st.subheader("Step 1 — Upload Job Description(s)")
jd_files = st.file_uploader("Upload JD files (PDF / DOCX / TXT)", type=["pdf","docx","txt"], accept_multiple_files=True)

RESUME_FOLDER = "resumes"
os.makedirs(RESUME_FOLDER, exist_ok=True)

# ---------- Optionally allow recruiter to refresh resume list ----------
st.subheader("Resume store")
st.write(f"Resumes folder: {RESUME_FOLDER} — {len(os.listdir(RESUME_FOLDER))} files")

# ---------- Process each JD ----------
if jd_files:
    for jd_file in jd_files:
        st.markdown(f"---\n### 📄 JD: *{jd_file.name}*")
        jd_text = extract_text(jd_file)
        if not jd_text or jd_text.strip()=="":
            st.error("Could not extract text from JD. Use selectable text PDF or TXT/DOCX.")
            continue

        # wordcloud
        st.subheader("Word Cloud (JD)")
        fig = generate_wordcloud_figure(jd_text)
        st.pyplot(fig)

        # load resumes texts from folder
        resumes = []
        for fname in sorted(os.listdir(RESUME_FOLDER)):
            if fname.lower().endswith((".pdf",".docx",".txt")):
                path = os.path.join(RESUME_FOLDER, fname)
                text = extract_text(path)
                resumes.append({"filename": fname, "text": text})

        if not resumes:
            st.warning("No resumes found in the resumes folder. Ask applicants to upload.")
            continue

        # compute scores (TF-IDF + optional semantic via utils)
        rows = compute_scores_for_resumes(jd_text, resumes, alpha=0.7)

        # extract keywords and snippets & highlights
        jd_keywords = extract_keywords(jd_text, top_n=40)

        enriched = []
        for r in rows:
            snippets = extract_snippets(r["text"], jd_keywords, max_snips=3)
            snippet_html = ""
            if snippets:
                snippet_html = "<br>".join(highlight_in_html(s, jd_keywords) for s in snippets)
            else:
                snippet_html = highlight_in_html(r["text"][:400], jd_keywords)

            enriched.append({
                "Resume": r["filename"],
                "Match %": r["score"],
                "Matching Keywords": ", ".join([k for k in jd_keywords if k.lower() in (r["text"] or "").lower()])[:500],
                "Snippet": snippet_html
            })

        df = pd.DataFrame(enriched).sort_values(by="Match %", ascending=False).reset_index(drop=True)

        st.subheader("Matching Results (sorted)")
        st.dataframe(df[["Resume","Match %","Matching Keywords"]])

        st.subheader("Detailed Results")
        for idx, row in df.iterrows():
            st.markdown(f"*{row['Resume']}* — Match: *{row['Match %']}%*")
            if row["Matching Keywords"]:
                st.markdown(f"*Matched keywords:* {row['Matching Keywords']}")
            if row["Snippet"]:
                st.markdown(row["Snippet"], unsafe_allow_html=True)
            st.markdown("---")

        # downloads
        st.subheader("Download Reports")
        st.download_button("Download CSV", df_to_csv_bytes(df), file_name=f"matching_{jd_file.name}.csv", mime="text/csv")
        pdf_buf = df_to_pdf_bytes(df, title=f"Matches for {jd_file.name}")
        st.download_button("Download PDF", pdf_buf, file_name=f"matching_{jd_file.name}.pdf", mime="application/pdf")