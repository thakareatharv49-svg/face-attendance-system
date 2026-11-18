"""Flask web application for face-recognition attendance."""
import base64
import binascii
import logging
import os
import re
import secrets
import threading
import time
from pathlib import Path

import cv2
import face_recognition
import numpy as np
from flask import Flask, abort, flash, jsonify, redirect, render_template, request, url_for
from flask_login import LoginManager, UserMixin, current_user, login_required, login_user, logout_user
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

from database import get_all_attendance, get_attendance, get_dashboard_stats, init_db, mark_attendance

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
KNOWN_FACES_DIR = Path(os.environ.get("KNOWN_FACES_DIR", BASE_DIR / "known_faces"))
MAX_IMAGE_BYTES = 2 * 1024 * 1024
FACE_MATCH_TOLERANCE = float(os.environ.get("FACE_MATCH_TOLERANCE", "0.48"))
EAR_THRESHOLD = float(os.environ.get("EAR_THRESHOLD", "0.21"))
BLINK_CLOSED_FRAMES = 2
LIVENESS_TTL_SECONDS = 20
NAME_PATTERN = re.compile(r"^[\w .'-]{1,60}$", re.UNICODE)

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY") or secrets.token_hex(32),
    MAX_CONTENT_LENGTH=3 * 1024 * 1024,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "false").lower() == "true",
    REMEMBER_COOKIE_HTTPONLY=True,
    REMEMBER_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "false").lower() == "true",
)
csrf = CSRFProtect(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Please sign in to access the admin area."
login_manager.session_protection = "strong"

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)
KNOWN_FACES_DIR.mkdir(parents=True, exist_ok=True)
init_db()

# The app deliberately fails closed when admin credentials are not configured.
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD_HASH = os.environ.get("ADMIN_PASSWORD_HASH", "")
if not ADMIN_PASSWORD_HASH and os.environ.get("ADMIN_PASSWORD"):
    logger.warning("ADMIN_PASSWORD is configured in plaintext; use ADMIN_PASSWORD_HASH instead.")


class AdminUser(UserMixin):
    id = "admin"


@login_manager.user_loader
def load_user(user_id):
    return AdminUser() if user_id == "admin" else None


known_encodings = []
known_names = []
face_lock = threading.RLock()
liveness_lock = threading.Lock()
liveness_sessions = {}
login_attempts = {}


def load_known_faces():
    encodings, names = [], []
    for path in sorted(KNOWN_FACES_DIR.iterdir()):
        if path.suffix.lower() not in {".jpg", ".jpeg", ".png"} or not path.is_file():
            continue
        try:
            image = face_recognition.load_image_file(str(path))
            found = face_recognition.face_encodings(image)
            if len(found) != 1:
                logger.warning("Skipping %s: expected exactly one face, found %s", path.name, len(found))
                continue
            encodings.append(found[0])
            names.append(path.stem.replace("_", " "))
        except Exception:
            logger.exception("Could not load registered face: %s", path.name)
    return encodings, names


def refresh_known_faces():
    global known_encodings, known_names
    encodings, names = load_known_faces()
    with face_lock:
        known_encodings, known_names = encodings, names
    logger.info("Loaded %d registered face(s)", len(names))


def euclidean(p1, p2):
    return float(np.linalg.norm(np.asarray(p1, dtype=float) - np.asarray(p2, dtype=float)))


def eye_aspect_ratio(points):
    horizontal = euclidean(points[0], points[3])
    if horizontal <= 0:
        return 1.0
    return (euclidean(points[1], points[5]) + euclidean(points[2], points[4])) / (2.0 * horizontal)


def decode_image(data_uri):
    if not isinstance(data_uri, str) or "," not in data_uri:
        raise ValueError("A valid camera image is required.")
    header, encoded = data_uri.split(",", 1)
    if header not in ("data:image/jpeg;base64", "data:image/png;base64"):
        raise ValueError("Only JPEG and PNG camera frames are accepted.")
    if len(encoded) > MAX_IMAGE_BYTES * 2:
        raise ValueError("Image is too large. Please use a smaller camera frame.")
    try:
        raw = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("The camera image could not be decoded.") from exc
    if not raw or len(raw) > MAX_IMAGE_BYTES:
        raise ValueError("Image must be smaller than 2 MB.")
    image = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("The uploaded image is not a valid image.")
    height, width = image.shape[:2]
    if width < 160 or height < 120:
        raise ValueError("Camera frame resolution is too small.")
    if width > 1280:
        scale = 1280 / width
        image = cv2.resize(image, (1280, int(height * scale)))
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)


def recognize_one(rgb):
    locations = face_recognition.face_locations(rgb, model="hog")
    if len(locations) != 1:
        return None, None, len(locations)
    encodings = face_recognition.face_encodings(rgb, locations)
    if not encodings:
        return None, None, 1
    with face_lock:
        encs, names = list(known_encodings), list(known_names)
    if not encs:
        return None, encodings[0], 1
    distances = face_recognition.face_distance(encs, encodings[0])
    best = int(np.argmin(distances))
    if float(distances[best]) <= FACE_MATCH_TOLERANCE:
        return names[best], encodings[0], 1
    return None, encodings[0], 1


def process_liveness(client_id, name, rgb):
    """Require a fresh close-then-open blink for this single recognized face."""
    now = time.monotonic()
    landmarks = face_recognition.face_landmarks(rgb)
    if not landmarks:
        return False, False
    left = eye_aspect_ratio(landmarks[0].get("left_eye", []))
    right = eye_aspect_ratio(landmarks[0].get("right_eye", []))
    closed = (left + right) / 2.0 < EAR_THRESHOLD
    with liveness_lock:
        state = liveness_sessions.get(client_id)
        if not state or state["expires"] < now or state["name"] != name:
            state = {"name": name, "closed_frames": 0, "expires": now + LIVENESS_TTL_SECONDS}
            liveness_sessions[client_id] = state
        state["expires"] = now + LIVENESS_TTL_SECONDS
        if closed:
            state["closed_frames"] = min(state["closed_frames"] + 1, 10)
            return True, False
        verified = state["closed_frames"] >= BLINK_CLOSED_FRAMES
        state["closed_frames"] = 0
        if verified:
            liveness_sessions.pop(client_id, None)
        # Periodically discard expired sessions.
        if len(liveness_sessions) > 500:
            for key in [k for k, value in liveness_sessions.items() if value["expires"] < now]:
                liveness_sessions.pop(key, None)
        return False, verified


@app.after_request
def security_headers(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(self), microphone=(), geolocation=()")
    response.headers.setdefault("Cache-Control", "no-store")
    return response


@app.errorhandler(413)
def too_large(_error):
    if request.path == "/process_frame":
        return jsonify({"error": "Request is too large."}), 413
    return "Upload too large.", 413


@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "face-attendance"})


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/process_frame", methods=["POST"])
def process_frame():
    payload = request.get_json(silent=True) or {}
    client_id = payload.get("client_id", "")
    if not isinstance(client_id, str) or not re.fullmatch(r"[a-f0-9-]{20,64}", client_id):
        return jsonify({"error": "Invalid kiosk session. Refresh this page."}), 400
    try:
        rgb = decode_image(payload.get("image"))
        name, _encoding, face_count = recognize_one(rgb)
        if face_count == 0:
            liveness_sessions.pop(client_id, None)
            return jsonify({"status": "no_face", "message": "Position your face inside the camera."})
        if face_count > 1:
            liveness_sessions.pop(client_id, None)
            return jsonify({"status": "multiple_faces", "message": "Only one person should stand in front of the camera."})
        if not name:
            liveness_sessions.pop(client_id, None)
            return jsonify({"status": "unknown", "message": "Face not registered. Please contact the administrator."})
        closed, verified = process_liveness(client_id, name, rgb)
        if verified:
            marked = mark_attendance(name)
            return jsonify({
                "status": "marked" if marked else "already_marked",
                "name": name,
                "marked": marked,
                "message": f"Attendance marked for {name}." if marked else f"{name} is already marked today.",
            })
        return jsonify({
            "status": "blink" if closed else "recognized",
            "name": name,
            "message": "Blink and reopen your eyes to confirm attendance." if not closed else "Blink detected. Open your eyes to confirm.",
        })
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception:
        logger.exception("Frame processing failed")
        return jsonify({"error": "Could not process this frame. Please try again."}), 500


def login_is_throttled(ip):
    now = time.monotonic()
    attempts = [stamp for stamp in login_attempts.get(ip, []) if now - stamp < 300]
    login_attempts[ip] = attempts
    return len(attempts) >= 8


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("admin_dashboard"))
    error = None
    if request.method == "POST":
        ip = request.remote_addr or "unknown"
        if login_is_throttled(ip):
            error = "Too many attempts. Wait five minutes and try again."
        else:
            username = request.form.get("username", "")
            password = request.form.get("password", "")
            configured_password = bool(ADMIN_PASSWORD_HASH or os.environ.get("ADMIN_PASSWORD"))
            valid_password = (
                check_password_hash(ADMIN_PASSWORD_HASH, password)
                if ADMIN_PASSWORD_HASH else
                secrets.compare_digest(password, os.environ.get("ADMIN_PASSWORD", ""))
            )
            if configured_password and secrets.compare_digest(username, ADMIN_USERNAME) and valid_password:
                login_attempts.pop(ip, None)
                login_user(AdminUser(), remember=False, fresh=True)
                return redirect(url_for("admin_dashboard"))
            login_attempts.setdefault(ip, []).append(time.monotonic())
            error = "Invalid username or password."
    return render_template("login.html", error=error)


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("You have been signed out.", "success")
    return redirect(url_for("login"))


@app.route("/admin")
@login_required
def admin_dashboard():
    date_from = request.args.get("from", "").strip() or None
    date_to = request.args.get("to", "").strip() or None
    name = request.args.get("name", "").strip() or None
    records = get_attendance(date_from, date_to, name)
    return render_template("admin.html", records=records, stats=get_dashboard_stats(),
                           date_from=date_from or "", date_to=date_to or "", search_name=name or "")


@app.route("/admin/register", methods=["GET", "POST"])
@login_required
def register():
    message = None
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        data_uri = request.form.get("image", "")
        if not NAME_PATTERN.fullmatch(name):
            message = "Use 1–60 letters, numbers, spaces, apostrophes, dots, or hyphens."
        else:
            safe_name = secure_filename(name)
            if not safe_name:
                message = "Please enter a valid name."
            else:
                path = KNOWN_FACES_DIR / f"{safe_name}.jpg"
                if path.exists():
                    message = "A person with this name is already registered."
                else:
                    try:
                        rgb = decode_image(data_uri)
                        encodings = face_recognition.face_encodings(rgb)
                        if len(encodings) != 1:
                            message = "Exactly one clear face must be visible. Please try again."
                        else:
                            bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
                            if not cv2.imwrite(str(path), bgr):
                                raise OSError("Could not save the registration photo.")
                            refresh_known_faces()
                            flash(f"{name} was registered successfully.", "success")
                            return redirect(url_for("people_list"))
                    except ValueError as exc:
                        message = str(exc)
                    except Exception:
                        logger.exception("Registration failed")
                        message = "Registration failed. Please try again."
    return render_template("register.html", message=message)


@app.route("/admin/people")
@login_required
def people_list():
    people = []
    for path in sorted(KNOWN_FACES_DIR.iterdir()):
        if path.suffix.lower() in {".jpg", ".jpeg", ".png"} and path.is_file():
            people.append(path.stem.replace("_", " "))
    return render_template("people.html", people=people)


@app.route("/admin/people/delete/<name>", methods=["POST"])
@login_required
def delete_person(name):
    safe_name = secure_filename(name)
    if not safe_name or safe_name != name:
        abort(400)
    deleted = False
    for suffix in (".jpg", ".jpeg", ".png"):
        path = KNOWN_FACES_DIR / f"{safe_name}{suffix}"
        if path.exists() and path.is_file():
            path.unlink()
            deleted = True
    if deleted:
        refresh_known_faces()
        flash(f"{name.replace('_', ' ')} was removed.", "success")
    else:
        flash("Person not found.", "warning")
    return redirect(url_for("people_list"))


@app.route("/admin/export.csv")
@login_required
def export_csv():
    import csv
    import io
    from flask import Response
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Name", "Timestamp"])
    for row in get_attendance(
        request.args.get("from") or None,
        request.args.get("to") or None,
        request.args.get("name") or None,
        limit=10000,
    ):
        writer.writerow(row)
    return Response("\ufeff" + output.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=attendance.csv"})


@app.cli.command("create-admin-hash")
def create_admin_hash():
    from werkzeug.security import generate_password_hash
    import getpass
    password = getpass.getpass("New admin password: ")
    if len(password) < 12:
        raise SystemExit("Use at least 12 characters.")
    print(generate_password_hash(password))


refresh_known_faces()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=False)
