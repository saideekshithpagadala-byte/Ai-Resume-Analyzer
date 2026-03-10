# AI Resume Analyzer

This project is a web-based **AI Resume Analyzer** that helps job seekers improve their resumes using **Artificial Intelligence** and **Natural Language Processing (NLP)**.

It supports:
- Uploading resumes in **PDF** or **DOCX** format
- Automatic text extraction and NLP-based skill/section detection
- **ATS compatibility** checks (structure, headings, formatting)
- **Job description matching** with resume skills
- **Scoring** (overall resume, ATS, job match) from 0–100
- Detailed suggestions and **downloadable PDF feedback reports**
- A **dashboard** with analysis history and score trends (Chart.js)

## Tech Stack

- **Frontend**: HTML, CSS, Bootstrap 5, Chart.js, Jinja templates
- **Backend**: Python, Flask, Flask-SQLAlchemy, Flask-Bcrypt
- **NLP / AI**: spaCy, PyPDF2, docx2txt, custom heuristics
- **Database**: SQLite by default (easily configurable to MySQL)

## Project Structure (high level)

- `app.py` – Flask application, routes, models, and configuration
- `templates/` – Jinja templates for Home, Login/Register, Upload, Analysis Result, Dashboard
- `static/css/styles.css` – Custom styling
- `static/js/main.js` – Placeholder for additional JS
- `utils/nlp_analyzer.py` – Resume text extraction, NLP logic, scoring, ATS checks
- `utils/pdf_report.py` – PDF report generation
- `requirements.txt` – Python dependencies

## Setup Instructions

1. **Create and activate a virtual environment** (recommended).

2. **Install dependencies**:
python -m venv venv
.\venv\Scripts\activate 
   ```bash
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   ```

3. (Optional) **Configure database**:

   - By default, the app uses an SQLite database file `resume_analyzer.db`.
   - To use MySQL, set the `DATABASE_URL` environment variable, e.g.:
     - `mysql+pymysql://username:password@host:3306/database_name`

4. **Run the application**:

   ```bash
   python app.py
   ```

5. Open your browser at:

   - `http://127.0.0.1:5000` (or `http://localhost:5000`)

## Usage

1. Register a new user account.
2. Log in and go to the **Upload Resume** page.
3. Upload a **PDF/DOCX** resume and optionally paste a **job description**.
4. View:
   - **Resume score**, **ATS score**, and **job match %**
   - Detected and missing skills
   - AI-generated suggestions and keyword recommendations
   - **Radar chart** and **history line chart** (on the dashboard)
5. Download a **PDF feedback report** for presentations or record-keeping.

## Notes

- This project is designed to be **hackathon-friendly** and easy to demo.
- You can extend it by:
  - Adding more sophisticated NLP models
  - Customizing scoring for specific job roles/industries
  - Integrating with external job APIs or ATS systems.

