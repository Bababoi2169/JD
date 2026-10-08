from flask import Flask, render_template, request
from utils import extract_text, generate_quiz, extract_requirements
from retrieval import get_relevant_questions
import uuid
from flask import redirect, url_for

QUIZZES = {}  # quiz_id -> list of questions (in memory, resets on restart)

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        resume_text = extract_text(request.files["resume"])
        jd_text = request.form["jd"]
        req = extract_requirements(resume_text, jd_text)
        bank = get_relevant_questions(req["queries"], req.get("role"), max_total=10)
        questions = generate_quiz(resume_text, jd_text, bank)
        quiz_id = str(uuid.uuid4())
        QUIZZES[quiz_id] = questions
        return redirect(url_for("quiz", quiz_id=quiz_id))
    return render_template("index.html")

@app.route("/quiz/<quiz_id>")
def quiz(quiz_id):
    questions = QUIZZES.get(quiz_id)
    if not questions:
        return redirect(url_for("index"))
    return render_template("quiz.html", questions=questions, quiz_id=quiz_id)

@app.route("/quiz/<quiz_id>/submit", methods=["POST"])
def submit(quiz_id):
    questions = QUIZZES.get(quiz_id)
    if not questions:
        return redirect(url_for("index"))
    results, score = [], 0
    for i, q in enumerate(questions):
        picked = int(request.form.get(f"q{i}", -1))
        correct = picked == q["correct_index"]
        score += correct
        results.append({**q, "picked": picked, "correct": correct})
    weak = sorted({r["topic"] for r in results if not r["correct"]})
    return render_template("results.html", results=results,
                           score=score, total=len(results), weak=weak)
if __name__ == "__main__":
    app.run(debug=True)
