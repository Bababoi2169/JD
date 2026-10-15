# PrepMate

AI-powered interview practice. Upload a resume and paste a job description, and PrepMate builds a personalized quiz, grades your answers, shows your skill gaps, and tracks your progress.

Built with Python, Flask, Groq and ChromaDB using Retrieval-Augmented Generation (RAG).

## Features

- **Personalized quiz** from your resume and a job description, split into easy, medium and hard sections
- **Two answer styles:** type your answers (graded by AI with feedback on what you covered and missed) or multiple choice
- **Selectable length:** 3, 5 or 7 questions per level
- **RAG grounding:** questions are adapted from a bank of real interview questions retrieved by role, topic and difficulty
- **Skill gap report:** strong, partial and missing skills compared to the job description, with a tip for each gap
- **Progress tracking:** every quiz and attempt is saved in SQLite, with a history page
- **PDF export:** the quiz with its answer key, or a full report with your answers, score and feedback
- **Scanned PDF support (optional):** falls back to OCR when a resume has no selectable text

## How it works

1. The resume (PDF or DOCX) is parsed to text and combined with the job description. If a PDF has no selectable text, OCR is attempted (when installed).
2. An LLM extracts the target role, the key skills to test, and the skill gap report.
3. Each skill is searched in the ChromaDB question bank, filtered by role and difficulty.
4. The retrieved questions are passed to the LLM, which writes the quiz.
5. Answers are scored (multiple choice) or graded by the LLM against key points (typed).
6. Results are saved to SQLite and shown with feedback, weak topics and the skill gap report.

## Setup

Requires Python 3.10 or newer and a [Groq API key](https://console.groq.com).

```bash
git clone https://github.com/Bababoi2169/JD.git
cd JD
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # Windows: copy .env.example .env
```

Open `.env` and set your key:

```
GROQ_API_KEY=your_key_here
```

### Load the question bank

The question bank (`data/question_bank.json`) and its vocabulary (`data/vocab.json`) are included in the repo. The vector database (`chroma_db/`) is generated locally, so load the bank into it once:

```bash
python ingest.py --file data/question_bank.json
```

The first run downloads a small embedding model (about 80 MB). Re-running `ingest.py` is safe: entries are upserted, not duplicated.

Optional: `python generate_bank.py` regenerates a starter bank with Groq (many API calls, a few minutes). It overwrites `data/question_bank.json` and `data/vocab.json`, so review the output before ingesting it.

### Optional: OCR for scanned PDFs

Text-based PDFs and DOCX files work without this step. To also support scanned (image-only) PDFs, install the Tesseract OCR engine. The Python packages (`pymupdf`, `pytesseract`, `pillow`) are already in `requirements.txt`, but they need the Tesseract program itself:

- **Windows:** download the installer from [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki) and run it. Either add the install folder (usually `C:\Program Files\Tesseract-OCR`) to your PATH, or point to it in `utils.py`:
  ```python
  pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
  ```
- **macOS:** `brew install tesseract`
- **Linux (Debian/Ubuntu):** `sudo apt install tesseract-ocr`
- **Fedora:** `sudo dnf install tesseract`

Check it works with `tesseract --version`. If OCR is not installed, the app still runs and shows the "couldn't read enough text" message for scanned PDFs. OCR reads only the first 3 pages.

### Run

```bash
python app.py
```

Open http://127.0.0.1:5000.

## Project structure

```
.
├── app.py              Flask routes and quiz flow
├── utils.py            Resume parsing (with OCR fallback) and all Groq calls
├── retrieval.py        Question bank search
├── ingest.py           Loads data/question_bank.json into ChromaDB
├── generate_bank.py    Generates a starter question bank with Groq
├── db.py               SQLite storage for quizzes and attempts
├── pdf_export.py       PDF report generation (ReportLab)
├── config.py           Shared constants (Chroma path, collection name)
├── requirements.txt
├── .env.example
├── data/
│   ├── question_bank.json
│   └── vocab.json      Allowed roles, topics and difficulty levels
├── templates/          Jinja pages (index, quiz, results, history, ...)
└── static/style.css
```

## Configuration

- **Model:** set `MODEL` at the top of `utils.py`. Groq retires models from time to time, so if you see a "model not found" error, check the current model list on the Groq console.
- **Default quiz length:** `PER_LEVEL` in `utils.py`. The form lets users pick 3, 5 or 7.
- **Question bank vocabulary:** edit `data/vocab.json`. Roles and topics must match the bank entries exactly, because retrieval filters on them.

Question bank entry format:

```json
{
  "id": "bd-sql-001",
  "role": "backend developer",
  "topic": "SQL",
  "difficulty": "medium",
  "question": "What is the difference between INNER JOIN and LEFT JOIN?",
  "reference_answer": "INNER JOIN returns only matching rows; LEFT JOIN returns all left rows plus matches.",
  "tags": ["joins", "databases"]
}
```

## Notes and limitations

- Scanned (image-only) PDFs need the optional OCR setup above. Without Tesseract installed they are rejected. OCR is slower and less accurate than direct text extraction, and only the first 3 pages are read.
- The included question bank was generated with an LLM, so reference answers may contain errors. Review entries before relying on them, and consider adding questions from curated datasets.
- AI grading is useful feedback, not an exact score.
- There are no user accounts: the history page shows all attempts stored on that server.
- On free Groq tiers you may hit rate limits. The app retries automatically and shows a message if the service stays busy.
- `quiz.db` and `chroma_db/` are local data and are git-ignored. If you change the database columns, delete `quiz.db` so it is recreated.

## Authors

Nandini Mishra and Ayushmaan Agrahari, B.Tech CSE (Self Finance), IET Lucknow.
