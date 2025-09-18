
import os
import re
import io
import PyPDF2
import docx2txt
from collections import Counter
import pandas as pd
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# Optional semantic model (if installed). We try to import but it's optional.
try:
    from sentence_transformers import SentenceTransformer, util
    SEM_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
except Exception:
    SEM_MODEL = None

# spaCy optional for keyword extraction (if installed)
try:
    import spacy
    SPACY_NLP = spacy.load("en_core_web_sm")
except Exception:
    SPACY_NLP = None

# -------------- Text extraction ----------------
def extract_text_from_pdf(path_or_file):
    text = ""
    # accepts path string or file-like
    try:
        if isinstance(path_or_file, str):
            f = open(path_or_file, "rb")
            reader = PyPDF2.PdfReader(f)
        else:
            reader = PyPDF2.PdfReader(path_or_file)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        if isinstance(path_or_file, str):
            f.close()
    except Exception:
        return ""
    return text

def extract_text_from_docx(path_or_file):
    # docx2txt accepts path or uploaded file saved to disk. If file-like, save temp.
    if isinstance(path_or_file, str):
        return docx2txt.process(path_or_file) or ""
    else:
        tmp = f"/tmp/{getattr(path_or_file,'name','tmp_docx')}"
        with open(tmp, "wb") as f:
            f.write(path_or_file.read())
        text = docx2txt.process(tmp) or ""
        try:
            os.remove(tmp)
        except: pass
        return text

def extract_text_from_txt(path_or_file):
    if isinstance(path_or_file, str):
        with open(path_or_file, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    else:
        return path_or_file.read().decode("utf-8", errors="ignore")

def extract_text(fileobj):
    """Generic extract: fileobj may be path str or uploaded file-like with .name"""
    if isinstance(fileobj, str):
        ext = fileobj.split(".")[-1].lower()
    else:
        ext = getattr(fileobj, "name", "").split(".")[-1].lower()
    if ext == "pdf":
        return extract_text_from_pdf(fileobj)
    if ext == "docx":
        return extract_text_from_docx(fileobj)
    if ext in ("txt", "text"):
        return extract_text_from_txt(fileobj)
    return ""

# -------------- Simple NLP helpers ----------------
def _clean_tokens(text):
    text = (text or "").lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    tokens = [t for t in text.split() if len(t)>2]
    return tokens

def extract_keywords(text, top_n=20):
    """If spaCy available, use it; otherwise frequency-based."""
    if SPACY_NLP:
        doc = SPACY_NLP(text.lower())
        tokens = [token.lemma_ for token in doc if token.is_alpha and not token.is_stop]
        freq = Counter(tokens)
        return [w for w,_ in freq.most_common(top_n)]
    tokens = _clean_tokens(text)
    freq = Counter(tokens)
    return [w for w,_ in freq.most_common(top_n)]

# -------------- Similarity / Ranking ----------------
def tfidf_similarity(jd_text, resume_text):
    try:
        vect = TfidfVectorizer(stop_words="english")
        tfidf = vect.fit_transform([jd_text, resume_text])
        score = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]
        return float(score)
    except Exception:
        return 0.0

def semantic_similarity(jd_text, resume_text):
    if SEM_MODEL is None:
        return 0.0
    try:
        a = SEM_MODEL.encode(jd_text, convert_to_tensor=True)
        b = SEM_MODEL.encode(resume_text, convert_to_tensor=True)
        return float(util.pytorch_cos_sim(a,b).item())
    except Exception:
        return 0.0

def combined_score(jd_text, resume_text, alpha=0.7):
    """alpha weight to TF-IDF, (1-alpha) to semantic if available"""
    t = tfidf_similarity(jd_text, resume_text)
    s = semantic_similarity(jd_text, resume_text) if SEM_MODEL else 0.0
    if SEM_MODEL:
        return alpha * t + (1-alpha) * s
    else:
        return t

def compute_scores_for_resumes(jd_text, resumes_list, alpha=0.7):
    """
    resumes_list: list of dicts {"filename":..., "text":...}
    returns list of dicts with keys: filename, score (0..100), text
    """
    rows = []
    for r in resumes_list:
        sc = combined_score(jd_text, r["text"], alpha=alpha)
        rows.append({"filename": r["filename"], "score": round(sc*100,2), "text": r["text"]})
    rows.sort(key=lambda x: x["score"], reverse=True)
    return rows

# -------------- Snippets & highlights ----------------
def extract_snippets(resume_text, jd_keywords, max_snips=3):
    import re
    if not resume_text: return []
    sentences = re.split(r'(?<=[.!?]) +|\n+', resume_text)
    out = []
    jd_lower = [k.lower() for k in jd_keywords]
    for s in sentences:
        sl = s.lower()
        if any(k in sl for k in jd_lower):
            out.append(s.strip())
        if len(out) >= max_snips:
            break
    return out

def highlight_in_html(text, keywords, skill_set=None):
    """Return HTML snippet with <mark> highlights. skill_set marked green."""
    if not text: return ""
    import re
    out = text
    for kw in sorted(set(keywords), key=len, reverse=True):
        if not kw: continue
        pattern = re.compile(re.escape(kw), re.IGNORECASE)
        if skill_set and kw.lower() in set(s.lower() for s in skill_set):
            repl = r"<mark style='background: #90EE90'>\g<0></mark>"  # green
        else:
            repl = r"<mark style='background: #FFFF99'>\g<0></mark>"  # yellow
        out = pattern.sub(repl, out)
    return out

# -------------- Wordcloud & reporting ----------------
def generate_wordcloud_figure(text):
    wc = WordCloud(width=800, height=300, background_color="white").generate(text)
    fig, ax = plt.subplots(figsize=(10,4))
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    return fig

def df_to_csv_bytes(df):
    return df.to_csv(index=False).encode("utf-8")

def df_to_pdf_bytes(df, title="Matching Report"):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()
    elems = [Paragraph(title, styles["Title"]), Spacer(1,12)]
    for _, row in df.iterrows():
        elems.append(Paragraph(f"<b>{row.get('Resume','')}</b> — Match: {row.get('Match %','')}", styles["Normal"]))
        if row.get("Matching Keywords"):
            elems.append(Paragraph(f"Keywords: {row.get('Matching Keywords')}", styles["Normal"]))
        if row.get("Snippet"):
            snippet_text = re.sub("<.*?>", "", row.get("Snippet"))
            elems.append(Paragraph(snippet_text[:500], styles["Normal"]))
        elems.append(Spacer(1,12))
    doc.build(elems)
    buffer.seek(0)
    return buffer