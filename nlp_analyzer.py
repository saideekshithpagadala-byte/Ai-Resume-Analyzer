import os
from typing import Dict, List

import PyPDF2
import docx2txt

# spaCy is optional; the app falls back gracefully if unavailable
try:
    import spacy  # type: ignore
except ImportError:
    spacy = None  # type: ignore
    NLP = None
else:
    # Load spaCy model once if available
    try:
        NLP = spacy.load("en_core_web_sm")  # type: ignore
    except OSError:
        NLP = None


CORE_SKILLS = {
    "python",
    "java",
    "javascript",
    "react",
    "node.js",
    "flask",
    "django",
    "machine learning",
    "deep learning",
    "nlp",
    "sql",
    "mysql",
    "mongodb",
    "git",
    "docker",
    "kubernetes",
    "data analysis",
    "pandas",
    "tensorflow",
    "pytorch",
}

SECTION_KEYWORDS = {
    "education": ["education", "academic", "bachelor", "master", "university", "college"],
    "experience": ["experience", "employment", "work history", "professional"],
    "skills": ["skills", "technical skills", "key skills"],
    "projects": ["projects", "personal projects", "academic projects"],
}


def extract_text_from_file(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        text = []
        with open(path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text.append(page.extract_text() or "")
        return "\n".join(text)
    elif ext == ".docx":
        return docx2txt.process(path)
    else:
        raise ValueError("Unsupported file type")


def normalize_token(token: str) -> str:
    return token.strip().lower()


def extract_skills(text: str) -> List[str]:
    lower_text = text.lower()
    detected = set()

    for skill in CORE_SKILLS:
        if skill in lower_text:
            detected.add(skill)

    if NLP:
        doc = NLP(text)
        for chunk in doc.noun_chunks:
            token = normalize_token(chunk.text)
            if token in CORE_SKILLS:
                detected.add(token)

    return sorted(detected)


def analyze_sections(text: str) -> Dict[str, bool]:
    lower_text = text.lower()
    result = {}
    for section, keywords in SECTION_KEYWORDS.items():
        result[section] = any(kw in lower_text for kw in keywords)
    return result


def ats_compatibility_score(text: str) -> float:
    lower = text.lower()

    score = 50.0

    has_bullets = any(b in text for b in ["•", "-", "*"])
    if has_bullets:
        score += 10

    keywords = ["education", "experience", "skills", "projects", "summary"]
    headings = sum(1 for kw in keywords if kw in lower)
    score += min(headings * 5, 20)

    if "table" in lower or "<table" in lower:
        score -= 10
    if len(text) > 15000:
        score -= 10

    return max(0.0, min(100.0, score))


def job_description_skills(job_description: str) -> List[str]:
    if not job_description:
        return []
    skills = extract_skills(job_description)
    return skills


def job_match_score(resume_skills: List[str], jd_skills: List[str]) -> float:
    if not jd_skills:
        return 0.0
    resume_set = set(s.lower() for s in resume_skills)
    jd_set = set(s.lower() for s in jd_skills)
    overlap = resume_set & jd_set
    return round(len(overlap) / len(jd_set) * 100, 2)


def compute_resume_score(
    section_presence: Dict[str, bool], ats_score: float, match_score: float
) -> float:
    section_points = sum(10 for present in section_presence.values() if present)
    total = 0.4 * ats_score + 0.4 * match_score + section_points
    return round(max(0.0, min(100.0, total)), 2)


def generate_suggestions(
    section_presence: Dict[str, bool],
    resume_skills: List[str],
    jd_skills: List[str],
    ats_score: float,
    match_score: float,
) -> Dict[str, List[str]]:
    suggestions: List[str] = []
    keyword_suggestions: List[str] = []

    for section, present in section_presence.items():
        if not present:
            suggestions.append(f"Add a clear '{section.title()}' section to your resume.")

    if ats_score < 70:
        suggestions.append(
            "Improve ATS compatibility by using clear section headings, bullet points, and avoiding complex tables or graphics."
        )

    if match_score < 70 and jd_skills:
        missing = sorted(set(jd_skills) - set(s.lower() for s in resume_skills))
        if missing:
            suggestions.append(
                "Highlight or acquire these role-specific skills and mention them in your resume."
            )
            keyword_suggestions.extend(missing)

    if not suggestions:
        suggestions.append(
            "Your resume looks strong. Consider tailoring it even more to each job description for the best results."
        )

    return {"suggestions": suggestions, "keyword_suggestions": keyword_suggestions}


def analyze_resume(path: str, job_description: str) -> Dict:
    text = extract_text_from_file(path)

    sections = analyze_sections(text)
    resume_skills = extract_skills(text)
    jd_skills = job_description_skills(job_description)

    ats_score = ats_compatibility_score(text)
    match = job_match_score(resume_skills, jd_skills)
    resume_score = compute_resume_score(sections, ats_score, match)

    sug = generate_suggestions(sections, resume_skills, jd_skills, ats_score, match)

    if jd_skills:
        missing = sorted(set(jd_skills) - set(s.lower() for s in resume_skills))
    else:
        missing = []

    return {
        "extracted_text": text,
        "resume_score": resume_score,
        "ats_score": ats_score,
        "job_match_score": match,
        "detected_skills": resume_skills,
        "missing_skills": missing,
        "suggestions": sug["suggestions"],
        "keyword_suggestions": sug["keyword_suggestions"],
    }

