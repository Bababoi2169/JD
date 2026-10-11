import io
from xml.sax.saxutils import escape
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, KeepTogether

ss = getSampleStyleSheet()
H2 = ParagraphStyle("H2", parent=ss["Heading2"], textColor=colors.HexColor("#0B2545"),
                    spaceBefore=10, keepWithNext=1)
B = ParagraphStyle("B", parent=ss["BodyText"], fontSize=10, leading=14)
SM = ParagraphStyle("SM", parent=B, fontSize=9, textColor=colors.grey)
GOOD = ParagraphStyle("GOOD", parent=B, textColor=colors.HexColor("#15803d"))
BAD = ParagraphStyle("BAD", parent=B, textColor=colors.HexColor("#b91c1c"))

def t(x):
    # escape markup; cp1252 matches reportlab's built-in fonts, so unknown symbols become "?" instead of boxes
    return escape(str(x)).encode("cp1252", "replace").decode("cp1252")

def make_pdf(quiz, attempt=None):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm, title="Interview Quiz")
    mode = "Multiple choice" if quiz["mode"] == "mcq" else "Typed answers"
    s = [Paragraph("Interview Quiz Report" if attempt else "Interview Quiz with Answer Key", ss["Title"]),
         Paragraph(t(f"Role: {quiz['role'] or 'General'}  |  Mode: {mode}  |  Created: {quiz['created_at']}"), SM)]

    if attempt:
        s.append(Paragraph(f"Overall score: {attempt['score']}%", H2))
        if attempt["weak"]:
            s.append(Paragraph("<b>Topics to review:</b> " + t(", ".join(attempt["weak"])), B))

    gap = quiz.get("gap") or {}
    if any(gap.get(k) for k in ("matched", "partial", "missing")):
        s.append(Paragraph("Skill gap report", H2))
        for label, key in (("Strong", "matched"), ("Partial", "partial"), ("Missing", "missing")):
            if gap.get(key):
                s.append(Paragraph(f"<b>{label}:</b> " + t(", ".join(gap[key])), B))
        for tip in gap.get("tips", []):
            s.append(Paragraph(f"<b>{t(tip['skill'])}:</b> {t(tip['tip'])}", B))

    s.append(Paragraph("Questions and answers", H2))
    items = attempt["results"] if attempt else quiz["questions"]
    level = None
    for i, q in enumerate(items, 1):
        if q["difficulty"] != level:
            level = q["difficulty"]
            s.append(Paragraph(level.capitalize(), H2))
        block = [Paragraph(f"<b>{i}. {t(q['question'])}</b>", B)]

        if quiz["mode"] == "mcq":
            for j, opt in enumerate(q["options"]):
                right = j == q["correct_index"]
                picked = bool(attempt) and q.get("picked") == j
                tag = (" [correct]" if right else "") + (" [your answer]" if picked else "")
                style = GOOD if right else (BAD if picked else B)
                block.append(Paragraph(t(f"{'ABCD'[j]}. {opt}{tag}"), style))
            block.append(Paragraph("<i>Explanation:</i> " + t(q["explanation"]), B))
        else:
            if attempt:
                block.append(Paragraph("<b>Your answer:</b> " + t(q["answer"] or "(blank)"), B))
                block.append(Paragraph(f"<b>Result:</b> {t(q['verdict'].capitalize())} ({q['score']}%). {t(q['feedback'])}", B))
                if q.get("missed"):
                    block.append(Paragraph("<b>Missed:</b> " + t("; ".join(q["missed"])), BAD))
            block.append(Paragraph("<b>Model answer:</b> " + t(q["model_answer"]), GOOD))
            block.append(Paragraph("<b>Key points:</b> " + t("; ".join(q["key_points"])), B))

        block.append(Spacer(1, 8))
        s.append(KeepTogether(block))

    doc.build(s)
    buf.seek(0)
    return buf
