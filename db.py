import sqlite3, json
from contextlib import closing
from datetime import datetime

DB_PATH = "quiz.db"

def _db():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    with closing(_db()) as c, c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS quizzes (
            id TEXT PRIMARY KEY, created_at TEXT, mode TEXT, role TEXT,
            questions TEXT, gap TEXT);
        CREATE TABLE IF NOT EXISTS attempts (
            quiz_id TEXT PRIMARY KEY REFERENCES quizzes(id),
            submitted_at TEXT, score INTEGER, weak TEXT, results TEXT);
        """)

def save_quiz(quiz_id, mode, role, questions, gap):
    with closing(_db()) as c, c:
        c.execute("INSERT INTO quizzes VALUES (?,?,?,?,?,?)",
                  (quiz_id, datetime.now().isoformat(timespec="seconds"), mode, role,
                   json.dumps(questions), json.dumps(gap)))

def get_quiz(quiz_id):
    with closing(_db()) as c:
        r = c.execute("SELECT * FROM quizzes WHERE id=?", (quiz_id,)).fetchone()
    if not r:
        return None
    d = dict(r)
    d["questions"], d["gap"] = json.loads(d["questions"]), json.loads(d["gap"])
    return d

def save_attempt(quiz_id, score, weak, results):
    with closing(_db()) as c, c:
        c.execute("INSERT OR REPLACE INTO attempts VALUES (?,?,?,?,?)",
                  (quiz_id, datetime.now().isoformat(timespec="seconds"), score,
                   json.dumps(weak), json.dumps(results)))

def get_attempt(quiz_id):
    with closing(_db()) as c:
        r = c.execute("SELECT * FROM attempts WHERE quiz_id=?", (quiz_id,)).fetchone()
    if not r:
        return None
    d = dict(r)
    d["weak"], d["results"] = json.loads(d["weak"]), json.loads(d["results"])
    return d

def list_history():
    with closing(_db()) as c:
        rows = c.execute("""SELECT q.id, q.role, q.mode, a.submitted_at, a.score
                            FROM attempts a JOIN quizzes q ON q.id = a.quiz_id
                            ORDER BY a.submitted_at DESC""").fetchall()
    return [dict(r) for r in rows]
