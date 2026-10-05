from flask import Flask, render_template, request
from utils import extract_text, generate_quiz

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        resume_text = extract_text(request.files["resume"])
        jd_text = request.form["jd"]
        questions = generate_quiz(resume_text, jd_text)
        return render_template("quiz.html", questions=questions)
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
