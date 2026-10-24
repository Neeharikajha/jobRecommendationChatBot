import io
import os
import pdfplumber
import docx
from .llm import generate_json
from .prompts import RESUME_PARSER_SYSTEM

MAX_MB = 5

class ResumeError(Exception):
    pass

def extract_text(file) -> str:
    name = file.name.lower()
    if not name.endswith((".pdf", ".docx")):
        raise ResumeError("Only pdf or docx files are supported.")
    if file.size > MAX_MB * 1024 * 1024:
        raise ResumeError(f"File too large (max {MAX_MB} MB).")
    data = file.read()
    try:
        if name.endswith(".pdf"):
            with pdfplumber.open(io.BytesIO(data)) as pdf:
                text = "\n".join((p.extract_text() or "") for p in pdf.pages)
        else:
            d = docx.Document(io.BytesIO(data))
            text = "\n".join(p.text for p in d.paragraphs)
            for t in d.tables:
                for row in t.rows:
                    text += "\n" + " | ".join(c.text for c in row.cells)
    except Exception:
        raise ResumeError("Couldn't read this file. It may be corrupted or password-protected.")
    text = text.strip()
    if len(text) < 100:
        raise ResumeError("No readable text found (maybe a scanned image). Upload a text-based PDF or DOCX.")
    return text

def parse_resume(text: str) -> dict:
    try:
        data = generate_json(f"Resume text:\n{text[:12000]}", RESUME_PARSER_SYSTEM)
    except Exception:
        raise ResumeError("Couldn't analyze the resume right now. Please try again.")
    if not isinstance(data, dict) or not data.get("skills"):
        raise ResumeError("This doesn't look like a resume (no skills found).")
    return data