import uuid
from flask import Flask, render_template, request, redirect, url_for, send_file
from utils import extract_text, generate_quiz, extract_requirements, evaluate_answers
from retrieval import get_relevant_questions
from db import init_db, save_quiz, get_quiz, save_attempt, get_attempt, list_history
from pdf_export import make_pdf
from groq import RateLimitError

app = Flask(__name__)
init_db()
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB

def build_quiz(resume_text, jd_text, req, mode):
    bank = []
    for level in ["easy", "medium", "hard"]:
        bank += get_relevant_questions(req["queries"], req.get("role"), difficulty=level, max_total=4)
    return generate_quiz(resume_text, jd_text, bank, n=15, mode=mode)

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
            save_quiz(quiz_id, mode, req.get("role"), questions, req["gap"])
            return redirect(url_for("quiz", quiz_id=quiz_id))

        except (ValueError, RuntimeError) as e:
            return render_template("index.html", error=str(e))
        except RateLimitError:
            return render_template("index.html", error="The AI service is busy. Wait a minute and try again.", jd=request.form.get("jd", ""))
        except Exception:
            app.logger.exception("Quiz generation failed")
            return render_template("index.html", error="Something went wrong. Please try again.")
    return render_template("index.html")


@app.route("/quiz/<quiz_id>")
def quiz(quiz_id):
    q = get_quiz(quiz_id)
    if not q:
        return redirect(url_for("index"))
    if get_attempt(quiz_id):
        return redirect(url_for("results", quiz_id=quiz_id))
    return render_template("quiz.html", questions=q["questions"], mode=q["mode"], quiz_id=quiz_id)


@app.route("/quiz/<quiz_id>/submit", methods=["POST"])
def submit(quiz_id):
    quiz = get_quiz(quiz_id)
    if not quiz:
        return redirect(url_for("index"))
    questions, mode = quiz["questions"], quiz["mode"]

    if mode == "mcq":
        results = []
        for i, q in enumerate(questions):
            picked = int(request.form.get(f"q{i}", -1))
            results.append({**q, "picked": picked, "correct": picked == q["correct_index"]})
        score = round(100 * sum(r["correct"] for r in results) / len(results))
        weak = sorted({r["topic"] for r in results if not r["correct"]})
    else:
        items = [{**q, "answer": request.form.get(f"q{i}", "").strip()} for i, q in enumerate(questions)]
        try:
            graded = evaluate_answers(items)
        except Exception:
            app.logger.exception("Grading failed")
            return "Grading failed. Go back and submit again.", 500
        results = [{**it, **g} for it, g in zip(items, graded)]
        score = round(sum(r["score"] for r in results) / len(results))
        weak = sorted({r["topic"] for r in results if r["verdict"] != "correct"})

    save_attempt(quiz_id, score, weak, results)
    return redirect(url_for("results", quiz_id=quiz_id))


def summarize(mode, results):
    levels = {}
    for r in results:
        levels.setdefault(r["difficulty"], []).append(r)
    if mode == "mcq":
        return {k: [sum(x["correct"] for x in v), len(v)] for k, v in levels.items()}
    return {k: round(sum(x["score"] for x in v) / len(v)) for k, v in levels.items()}


@app.route("/quiz/<quiz_id>/results")
def results(quiz_id):
    quiz, att = get_quiz(quiz_id), get_attempt(quiz_id)
    if not quiz or not att:
        return redirect(url_for("index"))
    res, mode = att["results"], quiz["mode"]
    common = dict(results=res, weak=att["weak"], by_level=summarize(mode, res),
                  gap=quiz["gap"], quiz_id=quiz_id)
    if mode == "mcq":
        return render_template("results.html", score=sum(r["correct"] for r in res), total=len(res), **common)
    return render_template("results_text.html", score=att["score"], **common)


@app.route("/history")
def history():
    return render_template("history.html", attempts=list_history())


@app.route("/quiz/<quiz_id>/pdf")
def export_pdf(quiz_id):
    quiz = get_quiz(quiz_id)
    if not quiz:
        return redirect(url_for("index"))
    buf = make_pdf(quiz, get_attempt(quiz_id))
    return send_file(buf, mimetype="application/pdf", as_attachment=True,
                     download_name=f"interview-quiz-{quiz_id[:8]}.pdf")


if __name__ == "__main__":
    app.run(debug=True)
