# Resume/JD text extraction + Groq quiz generation

import os, json
from dotenv import load_dotenv
from groq import Groq
from pypdf import PdfReader
from docx import Document

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "openai/gpt-oss-120b"

def extract_text(file_storage) -> str:
    name = file_storage.filename.lower()
    if name.endswith(".pdf"):
        reader = PdfReader(file_storage.stream)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    elif name.endswith(".docx"):
        doc = Document(file_storage.stream)
        text = "\n".join(p.text for p in doc.paragraphs)
    else:
        raise ValueError("Unsupported file type")
    return text.strip()

def generate_quiz(resume_text: str, jd_text: str, n: int = 5) -> list[dict]:
    prompt = f"""You are an interview coach. Using the resume and job description below,
create {n} multiple-choice interview questions personalized to this candidate and role.

Return ONLY a JSON object: {{"questions": [{{
  "question": str,
  "options": [4 strings],
  "correct_index": int (0-3),
  "explanation": str,
  "topic": str,
  "difficulty": "easy" | "medium" | "hard",
  "tied_to": str (which resume item or JD requirement this targets)
}}]}}

RESUME:
{resume_text[:6000]}

JOB DESCRIPTION:
{jd_text[:4000]}"""

    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.7,
    )
    return json.loads(resp.choices[0].message.content)["questions"]

def extract_requirements(resume_text: str, jd_text: str) -> dict:
    vocab = json.load(open("data/vocab.json"))
    prompt = f"""From the job description and resume, return ONLY JSON:
{{"role": one of {vocab["roles"]} or null if none fit,
  "queries": [6-10 short skill/topic phrases (2-4 words) the interview should cover,
              prioritising JD requirements, especially ones weak or missing in the resume]}}

JOB DESCRIPTION:
{jd_text[:4000]}

RESUME:
{resume_text[:4000]}"""
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.2,
        max_tokens=1000,
    )
    return json.loads(resp.choices[0].message.content)
