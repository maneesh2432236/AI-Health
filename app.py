import base64
import json
import os
import sqlite3
import uuid
from datetime import datetime
from functools import wraps

from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from models.ai_model import ImageProcessingError, analyze_image_for_type

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "ai-health-mirror-pro-secret")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
DB_PATH = os.path.join(BASE_DIR, "database.db")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS analysis_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                analysis_type TEXT NOT NULL,
                image_path TEXT NOT NULL,
                result TEXT NOT NULL,
                recommendations TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """
        )
        conn.commit()


init_db()


def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)

    return wrapper


def save_uploaded_file(file_storage):
    if not file_storage or file_storage.filename == "":
        raise ValueError("Please select an image to continue.")

    filename = secure_filename(file_storage.filename)
    if not filename:
        raise ValueError("The selected file name is invalid.")

    ext = filename.rsplit(".", 1)[1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError("Unsupported file format. Please upload JPG, JPEG, or PNG images only.")

    unique_name = f"{uuid.uuid4().hex}_{filename}"
    file_path = os.path.join(UPLOAD_FOLDER, unique_name)
    file_storage.save(file_path)
    return file_path


def save_camera_image(data_url):
    if not data_url or "," not in data_url:
        raise ValueError("Camera image data is missing.")

    header, encoded = data_url.split(",", 1)
    if not header.startswith("data:image/"):
        raise ValueError("The captured image is invalid.")

    mime_type = header.split(":", 1)[1].split(";", 1)[0]
    extension = mime_type.split("/")[-1]
    if extension not in {"png", "jpg", "jpeg"}:
        raise ValueError("Camera output must be PNG, JPG, or JPEG.")

    missing_padding = len(encoded) % 4
    if missing_padding:
        encoded += "=" * (4 - missing_padding)

    try:
        image_data = base64.b64decode(encoded, validate=True)
    except Exception as exc:
        raise ValueError("Camera image could not be decoded.") from exc

    file_name = f"camera_{uuid.uuid4().hex}.{extension}"
    file_path = os.path.join(UPLOAD_FOLDER, file_name)
    with open(file_path, "wb") as file_obj:
        file_obj.write(image_data)

    return file_path


def save_analysis_record(user_id, analysis_type, image_path, result, recommendations):
    recommendations_text = json.dumps(recommendations, ensure_ascii=False)
    relative_path = os.path.relpath(image_path, os.path.join(BASE_DIR, "static")).replace("\\", "/")
    with get_db_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO analysis_history (user_id, analysis_type, image_path, result, recommendations, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, analysis_type, relative_path, result, recommendations_text, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )
        conn.commit()
        return cursor.lastrowid


@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return render_template("index.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        confirm_password = request.form.get("confirm_password") or ""

        if not all([name, email, password, confirm_password]):
            flash("All signup fields are required.", "danger")
            return render_template("signup.html")

        if password != confirm_password:
            flash("Passwords do not match. Please try again.", "danger")
            return render_template("signup.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "danger")
            return render_template("signup.html")

        with get_db_connection() as conn:
            existing_user = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
            if existing_user:
                flash("An account with this email already exists.", "danger")
                return render_template("signup.html")

            conn.execute(
                "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                (name, email, generate_password_hash(password)),
            )
            conn.commit()

        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""

        if not email or not password:
            flash("Email and password are required.", "danger")
            return render_template("login.html")

        with get_db_connection() as conn:
            user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

        if user is None:
            flash("Invalid email or password.", "danger")
            return render_template("login.html")

        if not check_password_hash(user["password"], password):
            flash("Incorrect password. Please try again.", "danger")
            return render_template("login.html")

        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        flash("Welcome back!", "success")
        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    user_id = session["user_id"]
    with get_db_connection() as conn:
        total_analyses = conn.execute("SELECT COUNT(*) as count FROM analysis_history WHERE user_id = ?", (user_id,)).fetchone()["count"]
        hair_analyses = conn.execute("SELECT COUNT(*) as count FROM analysis_history WHERE user_id = ? AND analysis_type = 'hair'", (user_id,)).fetchone()["count"]
        skin_analyses = conn.execute("SELECT COUNT(*) as count FROM analysis_history WHERE user_id = ? AND analysis_type = 'skin'", (user_id,)).fetchone()["count"]
        recent_analysis = conn.execute(
            "SELECT * FROM analysis_history WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
            (user_id,),
        ).fetchone()

    recent_data = dict(recent_analysis) if recent_analysis else None
    if recent_data:
        recent_data["recommendations"] = json.loads(recent_data["recommendations"]) if recent_data["recommendations"] else {}

    return render_template(
        "dashboard.html",
        user_name=session.get("user_name", "User"),
        total_analyses=total_analyses,
        hair_analyses=hair_analyses,
        skin_analyses=skin_analyses,
        recent_analysis=recent_data,
    )


@app.route("/hair-analysis", methods=["GET", "POST"])
@login_required
def hair_analysis():
    if request.method == "POST":
        return redirect(url_for("analyze_hair"))
    return render_template("hair_analysis.html")


@app.route("/skin-analysis", methods=["GET", "POST"])
@login_required
def skin_analysis():
    if request.method == "POST":
        return redirect(url_for("analyze_skin"))
    return render_template("skin_analysis.html")


@app.route("/analyze-hair", methods=["POST"])
@login_required
def analyze_hair():
    user_id = session["user_id"]
    try:
        if "image" in request.files and request.files["image"].filename:
            image_path = save_uploaded_file(request.files["image"])
        elif request.form.get("camera_data_url"):
            image_path = save_camera_image(request.form.get("camera_data_url"))
        else:
            raise ValueError("Please upload an image or capture a photo before analyzing.")

        result_data = analyze_image_for_type("hair", image_path)
        result_text = result_data.get("result", "Demo AI Analysis")
        analysis_id = save_analysis_record(
            user_id=user_id,
            analysis_type="hair",
            image_path=image_path,
            result=result_text,
            recommendations={
                "hair_care": result_data.get("hair_care", []),
                "diet": result_data.get("diet", []),
                "home_care": result_data.get("home_care", []),
                "daily_routine": result_data.get("daily_routine", []),
                "concern": result_data.get("concern", "General hair wellness overview"),
                "demo_label": result_data.get("demo_label", "Demo AI Analysis")
            },
        )
        flash("Hair analysis completed successfully.", "success")
        return redirect(url_for("result", analysis_id=analysis_id))
    except ImageProcessingError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("hair_analysis"))
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("hair_analysis"))
    except Exception as exc:
        flash(f"Analysis could not be completed: {exc}", "danger")
        return redirect(url_for("hair_analysis"))


@app.route("/analyze-skin", methods=["POST"])
@login_required
def analyze_skin():
    user_id = session["user_id"]
    try:
        if "image" in request.files and request.files["image"].filename:
            image_path = save_uploaded_file(request.files["image"])
        elif request.form.get("camera_data_url"):
            image_path = save_camera_image(request.form.get("camera_data_url"))
        else:
            raise ValueError("Please upload an image or capture a photo before analyzing.")

        result_data = analyze_image_for_type("skin", image_path)
        result_text = result_data.get("result", "Demo AI Analysis")
        analysis_id = save_analysis_record(
            user_id=user_id,
            analysis_type="skin",
            image_path=image_path,
            result=result_text,
            recommendations={
                "skin_care": result_data.get("skin_care", []),
                "diet": result_data.get("diet", []),
                "home_care": result_data.get("home_care", []),
                "daily_routine": result_data.get("daily_routine", []),
                "concern": result_data.get("concern", "General skin wellness overview"),
                "demo_label": result_data.get("demo_label", "Demo AI Analysis")
            },
        )
        flash("Skin analysis completed successfully.", "success")
        return redirect(url_for("result", analysis_id=analysis_id))
    except ImageProcessingError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("skin_analysis"))
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("skin_analysis"))
    except Exception as exc:
        flash(f"Analysis could not be completed: {exc}", "danger")
        return redirect(url_for("skin_analysis"))


@app.route("/result/<int:analysis_id>")
@login_required
def result(analysis_id):
    with get_db_connection() as conn:
        analysis = conn.execute(
            "SELECT * FROM analysis_history WHERE id = ? AND user_id = ?",
            (analysis_id, session["user_id"]),
        ).fetchone()

    if analysis is None:
        flash("The requested analysis was not found.", "danger")
        return redirect(url_for("dashboard"))

    analysis_data = dict(analysis)
    analysis_data["recommendations"] = json.loads(analysis["recommendations"]) if analysis["recommendations"] else {}
    analysis_data["image_url"] = "/" + analysis_data["image_path"].replace("\\", "/")
    return render_template("result.html", analysis=analysis_data)


@app.route("/history")
@login_required
def history():
    with get_db_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM analysis_history WHERE user_id = ? ORDER BY created_at DESC",
            (session["user_id"],),
        ).fetchall()

    analyses = []
    for row in rows:
        item = dict(row)
        item["recommendations"] = json.loads(row["recommendations"]) if row["recommendations"] else {}
        analyses.append(item)

    return render_template("history.html", analyses=analyses)


@app.route("/recommendations")
@login_required
def recommendations():
    return render_template("recommendations.html")


@app.route("/profile")
@login_required
def profile():
    user_id = session["user_id"]
    with get_db_connection() as conn:
        user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        total_analyses = conn.execute("SELECT COUNT(*) as count FROM analysis_history WHERE user_id = ?", (user_id,)).fetchone()["count"]

    if user is None:
        session.clear()
        flash("Your session is invalid. Please log in again.", "warning")
        return redirect(url_for("login"))

    return render_template("profile.html", user=dict(user), total_analyses=total_analyses)


@app.context_processor
def inject_user():
    return {
        "logged_in_user": session.get("user_name"),
        "current_year": datetime.now().year,
    }


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
