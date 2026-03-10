import os
from typing import Union

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
REPORT_DIR = os.path.join(BASE_DIR, "reports")
os.makedirs(REPORT_DIR, exist_ok=True)


def _wrap_text(text: str, max_chars: int = 90):
    if not text:
        return []
    words = text.split()
    lines = []
    current = []
    length = 0
    for w in words:
        if length + len(w) + 1 > max_chars:
            lines.append(" ".join(current))
            current = [w]
            length = len(w)
        else:
            current.append(w)
            length += len(w) + 1
    if current:
        lines.append(" ".join(current))
    return lines


def generate_report_pdf(analysis: Union[object, dict]) -> str:
    report_path = os.path.join(REPORT_DIR, f"analysis_{analysis.id}.pdf")
    c = canvas.Canvas(report_path, pagesize=A4)
    width, height = A4

    y = height - 50
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, y, "AI Resume Analysis Report")
    y -= 30

    c.setFont("Helvetica", 11)
    c.drawString(
        50, y, f"Resume score: {round(analysis.resume_score or 0, 2)} / 100"
    )
    y -= 15
    c.drawString(50, y, f"ATS compatibility: {round(analysis.ats_score or 0, 2)} / 100")
    y -= 15
    c.drawString(
        50,
        y,
        f"Job match: {round(analysis.job_match_score or 0, 2)} %",
    )
    y -= 25

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Detected skills:")
    y -= 15
    c.setFont("Helvetica", 10)
    skills = (analysis.detected_skills or "").split(",") if analysis.detected_skills else []
    if skills:
        c.drawString(60, y, ", ".join(skills))
        y -= 20
    else:
        c.drawString(60, y, "No specific skills detected.")
        y -= 20

    missing = (analysis.missing_skills or "").split(",") if analysis.missing_skills else []
    if missing:
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "Missing / recommended skills:")
        y -= 15
        c.setFont("Helvetica", 10)
        c.drawString(60, y, ", ".join(missing))
        y -= 20

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Suggestions:")
    y -= 15
    c.setFont("Helvetica", 10)
    suggestions_text = analysis.suggestions or ""
    for para in suggestions_text.split("\n"):
        for line in _wrap_text(para, max_chars=90):
            if y < 80:
                c.showPage()
                y = height - 50
                c.setFont("Helvetica", 10)
            c.drawString(60, y, f"- {line}")
            y -= 14
        y -= 6

    c.showPage()
    c.save()
    return report_path

