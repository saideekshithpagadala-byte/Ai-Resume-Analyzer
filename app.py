import os
import datetime
from functools import wraps

from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import jwt

from werkzeug.utils import secure_filename

from utils.nlp_analyzer import analyze_resume
from utils.pdf_report import generate_report_pdf


BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def create_app():
    app = Flask(__name__)

    # In production, load from environment / .env
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
    # Default to SQLite for easy local demo; replace with MySQL URI as needed
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL",
        "sqlite:///" + os.path.join(BASE_DIR, "resume_analyzer.db"),
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["UPLOAD_FOLDER"] = os.path.join(BASE_DIR, "uploads")
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    bcrypt.init_app(app)

    with app.app_context():
        db.create_all()

    register_routes(app)
    return app


db = SQLAlchemy()
bcrypt = Bcrypt()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    analyses = db.relationship("ResumeAnalysis", backref="user", lazy=True)

    def set_password(self, password: str):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password: str) -> bool:
        return bcrypt.check_password_hash(self.password_hash, password)


class ResumeAnalysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    original_filename = db.Column(db.String(255))
    extracted_text = db.Column(db.Text)
    job_description = db.Column(db.Text)

    resume_score = db.Column(db.Float)
    ats_score = db.Column(db.Float)
    job_match_score = db.Column(db.Float)

    detected_skills = db.Column(db.Text)  # comma-separated
    missing_skills = db.Column(db.Text)  # comma-separated
    keyword_suggestions = db.Column(db.Text)
    suggestions = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)

    return wrapper


def register_routes(app: Flask):
    @app.route("/")
    def home():
        return render_template("home.html")

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")

            if not name or not email or not password:
                return render_template("register.html", error="All fields are required.")

            if User.query.filter_by(email=email).first():
                return render_template("register.html", error="Email already registered.")

            user = User(name=name, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()

            session["user_id"] = user.id
            session["user_name"] = user.name
            return redirect(url_for("upload_resume"))

        return render_template("register.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")

            user = User.query.filter_by(email=email).first()
            if not user or not user.check_password(password):
                return render_template("login.html", error="Invalid email or password.")

            session["user_id"] = user.id
            session["user_name"] = user.name
            return redirect(url_for("upload_resume"))

        return render_template("login.html")

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("home"))

    @app.route("/upload", methods=["GET", "POST"])
    @login_required
    def upload_resume():
        if request.method == "POST":
            file = request.files.get("resume")
            job_description = request.form.get("job_description", "")

            if not file or file.filename == "":
                return render_template(
                    "upload.html", error="Please upload a resume file."
                )

            filename = secure_filename(file.filename)
            ext = os.path.splitext(filename)[1].lower()
            if ext not in [".pdf", ".docx"]:
                return render_template(
                    "upload.html",
                    error="Unsupported file type. Please upload PDF or DOCX.",
                )

            save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(save_path)

            try:
                analysis = analyze_resume(save_path, job_description)
            except Exception as exc:  # broad for demo
                return render_template(
                    "upload.html",
                    error=f"Failed to analyze resume: {exc}",
                )

            user_id = session["user_id"]
            analysis_record = ResumeAnalysis(
                user_id=user_id,
                original_filename=filename,
                extracted_text=analysis["extracted_text"],
                job_description=job_description,
                resume_score=analysis["resume_score"],
                ats_score=analysis["ats_score"],
                job_match_score=analysis["job_match_score"],
                detected_skills=",".join(analysis["detected_skills"]),
                missing_skills=",".join(analysis["missing_skills"]),
                keyword_suggestions="\n".join(analysis["keyword_suggestions"]),
                suggestions="\n".join(analysis["suggestions"]),
            )
            db.session.add(analysis_record)
            db.session.commit()

            return redirect(url_for("analysis_result", analysis_id=analysis_record.id))

        return render_template("upload.html")

    @app.route("/analysis/<int:analysis_id>")
    @login_required
    def analysis_result(analysis_id: int):
        record = ResumeAnalysis.query.filter_by(
            id=analysis_id, user_id=session["user_id"]
        ).first_or_404()

        detected_skills = (
            record.detected_skills.split(",") if record.detected_skills else []
        )
        missing_skills = (
            record.missing_skills.split(",") if record.missing_skills else []
        )

        return render_template(
            "analysis_result.html",
            analysis=record,
            detected_skills=detected_skills,
            missing_skills=missing_skills,
        )

    @app.route("/dashboard")
    @login_required
    def dashboard():
        analyses = (
            ResumeAnalysis.query.filter_by(user_id=session["user_id"])
            .order_by(ResumeAnalysis.created_at.desc())
            .all()
        )
        return render_template("dashboard.html", analyses=analyses)

    @app.route("/api/analysis/<int:analysis_id>/chart-data")
    @login_required
    def analysis_chart_data(analysis_id: int):
        record = ResumeAnalysis.query.filter_by(
            id=analysis_id, user_id=session["user_id"]
        ).first_or_404()
        return jsonify(
            {
                "resume_score": record.resume_score or 0,
                "ats_score": record.ats_score or 0,
                "job_match_score": record.job_match_score or 0,
            }
        )

    @app.route("/report/<int:analysis_id>")
    @login_required
    def download_report(analysis_id: int):
        record = ResumeAnalysis.query.filter_by(
            id=analysis_id, user_id=session["user_id"]
        ).first_or_404()

        report_path = generate_report_pdf(record)
        return send_file(
            report_path,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"resume_analysis_{analysis_id}.pdf",
        )


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)

