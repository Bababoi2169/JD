import uuid
from flask import Flask, render_template, request, redirect, url_for
from utils import extract_text, generate_quiz, extract_requirements, evaluate_answers
from retrieval import get_relevant_questions
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB

QUIZZES = {}  # quiz_id -> list of questions (in memory, resets on restart)

def build_quiz(resume_text, jd_text, req, mode, per_level=5):
    def one(level):
        bank = get_relevant_questions(req["queries"], req.get("role"), difficulty=level, max_total=8)
        return generate_quiz(resume_text, jd_text, bank, n=per_level, difficulty=level, mode=mode)
    with ThreadPoolExecutor(max_workers=3) as ex:   # runs the 3 calls in parallel
        parts = list(ex.map(one, ["easy", "medium", "hard"]))
    return [q for part in parts for q in part]

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        try:
            resume_file = request.files.get("resume")
            if not resume_file or not resume_file.filename:
                raise ValueError("Please upload a resume.")
            jd_text = request.form.get("jd", "").strip()
            if len(jd_text) < 50:
                raise ValueError("Please paste a longer job description.")

            resume_text = extract_text(resume_file)
            req = extract_requirements(resume_text, jd_text)
            mode = request.form.get("mode", "text")
            questions = build_quiz(resume_text, jd_text, req, mode)
            quiz_id = str(uuid.uuid4())
            QUIZZES[quiz_id] = {"mode": mode, "questions": questions}
            return redirect(url_for("quiz", quiz_id=quiz_id))
        except (ValueError, RuntimeError) as e:
            return render_template("index.html", error=str(e))
        except Exception:
            app.logger.exception("Quiz generation failed")
            return render_template("index.html", error="Something went wrong. Please try again.")
    return render_template("index.html")


@app.route("/quiz/<quiz_id>")
def quiz(quiz_id):
    quiz = QUIZZES.get(quiz_id)
    if not quiz:
        return redirect(url_for("index"))
    return render_template("quiz.html", questions=quiz["questions"], mode=quiz["mode"], quiz_id=quiz_id)


@app.route("/quiz/<quiz_id>/submit", methods=["POST"])
def submit(quiz_id):
    quiz = QUIZZES.get(quiz_id)
    if not quiz:
        return redirect(url_for("index"))
    questions, mode = quiz["questions"], quiz["mode"]

    if mode == "mcq":
        results, score, by_level = [], 0, {}
        for i, q in enumerate(questions):
            picked = int(request.form.get(f"q{i}", -1))
            correct = picked == q["correct_index"]
            score += correct
            results.append({**q, "picked": picked, "correct": correct})
            s = by_level.setdefault(q["difficulty"], [0, 0])
            s[0] += correct
            s[1] += 1
        weak = sorted({r["topic"] for r in results if not r["correct"]})
        return render_template("results.html", results=results, score=score,
                               total=len(results), weak=weak, by_level=by_level)

    items = [{**q, "answer": request.form.get(f"q{i}", "").strip()} for i, q in enumerate(questions)]
    try:
        graded = evaluate_answers(items)
    except Exception:
        app.logger.exception("Grading failed")
        return "Grading failed. Go back and submit again.", 500

    results = [{**it, **g} for it, g in zip(items, graded)]
    score = round(sum(r["score"] for r in results) / len(results))
    levels = {}
    for r in results:
        levels.setdefault(r["difficulty"], []).append(r["score"])
    by_level = {k: round(sum(v) / len(v)) for k, v in levels.items()}
    weak = sorted({r["topic"] for r in results if r["verdict"] != "correct"})
    return render_template("results_text.html", results=results, score=score,
                           by_level=by_level, weak=weak)


if __name__ == "__main__":
    app.run(debug=True)
