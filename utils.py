import os
import re
import io
import PyPDF2
import docx2txt
import pandas as pd
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from collections import Counter
import spacy

# Load NLP model
nlp = spacy.load("en_core_web_sm")

# Extract text from PDF
def extract_text_from_pdf(file):
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

# Extract text from DOCX
def extract_text_from_docx(file):
    return docx2txt.process(file)

# Extract text based on file type
def extract_text(file):
    ext = file.name.split(".")[-1].lower()
    if ext == "pdf":
        return extract_text_from_pdf(file)
    elif ext == "docx":
        return extract_text_from_docx(file)
    return ""

# Extract keywords using spaCy
def extract_keywords(text, top_n=15):
    doc = nlp(text.lower())
    words = [token.text for token in doc if token.is_alpha and not token.is_stop]
    freq = Counter(words)
    return [word for word, _ in freq.most_common(top_n)]

# Generate word cloud
def generate_wordcloud(text):
    wc = WordCloud(width=800, height=400, background_color="white").generate(text)
    fig, ax = plt.subplots()
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    return fig

# Compute similarity between JD and resumes
def compute_similarity(jd_text, resumes):
    texts = [jd_text] + [r["text"] for r in resumes]
    vectorizer = TfidfVectorizer(stop_words="english")
    vectors = vectorizer.fit_transform(texts)
    scores = cosine_similarity(vectors[0:1], vectors[1:]).flatten()
    return scores, vectorizer

# Extract snippets from resumes
def extract_snippets(resume_text, jd_keywords, num_snippets=3):
    snippets = []
    sentences = re.split(r'(?<=[.!?]) +|\n+', resume_text)
    for sentence in sentences:
        if any(k.lower() in sentence.lower() for k in jd_keywords):
            snippets.append(sentence.strip())
        if len(snippets) >= num_snippets:
            break
    return snippets

# Convert dataframe to CSV bytes
def df_to_csv_bytes(df):
    return df.to_csv(index=False).encode("utf-8")

# Convert dataframe to PDF bytes
def df_to_pdf_bytes(df, title="Resume Matching Report"):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()
    elements = [Paragraph(title, styles["Title"]), Spacer(1, 12)]
    for _, row in df.iterrows():
        elements.append(Paragraph(f"<b>Resume:</b> {row['Resume']}", styles["Normal"]))
        elements.append(Paragraph(f"<b>Match %:</b> {row['Match %']}%", styles["Normal"]))
        elements.append(Paragraph(f"<b>Matching Keywords:</b> {row['Matching Keywords']}", styles["Normal"]))
        if row.get("Snippet"):
            elements.append(Paragraph(f"<b>Snippet:</b> {row['Snippet'][:400]}", styles["Normal"]))
        elements.append(Spacer(1, 12))
    doc.build(elements)
    buffer.seek(0)
    return buffer

