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

## How it works

1. The resume (PDF or DOCX) is parsed to text and combined with the job description.
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

### Build the question bank

The vector database (`chroma_db/`) is not committed, so build it once from the JSON files in `data/`:

```bash
python ingest.py --file data/question_bank.json
```

If `data/question_bank.json` does not exist yet, generate a starter bank first (this makes many Groq calls and takes a few minutes), then review it before ingesting:

```bash
python generate_bank.py
```

Re-running `ingest.py` is safe: entries are upserted, not duplicated.

### Run

```bash
python app.py
```

Open http://127.0.0.1:5000.

## Project structure

```
.
├── app.py              Flask routes and quiz flow
├── utils.py            Resume parsing and all Groq calls (requirements, quiz, grading)
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

- Scanned (image-only) PDFs are not supported, because text is extracted directly from the file.
- Questions in the generated bank are LLM-written, so review them for accuracy before relying on the reference answers.
- AI grading is useful feedback, not an exact score.
- There are no user accounts: the history page shows all attempts stored on that server.
- On free Groq tiers you may hit rate limits. The app retries automatically and shows a message if the service stays busy.
- `quiz.db` and `chroma_db/` are local data and are git-ignored. If you change the database columns, delete `quiz.db` so it is recreated.

## Authors

Nandini Mishra and Ayushmaan Agrahari, B.Tech CSE (Self Finance), IET Lucknow.
