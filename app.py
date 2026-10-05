import os
from dotenv import load_dotenv
from groq import Groq
from pypdf import PdfReader
from flask import Flask, render_template

app=Flask(__name__)
load_dotenv()

client =Groq(api_key=os.environ.get("GROQ_API_KEY"))

reader=PdfReader('test.pdf')
page=reader.pages[0]

test=client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[{"role": "user","content": f" list all the projcets name in the resume: {page.extract_text()} add<br> tags for each project."}])

@app.route('/')
def welcome():
    return render_template("home.html",projects=test.choices[0].message.content)

if(__name__ == "__main__"):
    app.run(debug=True)
