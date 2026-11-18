from flask import Flask, render_template, request, jsonify, redirect, url_for, abort
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import face_recognition
import numpy as np
import cv2
import os
import math
import base64
import re
from functools import wraps
from database import (init_db, mark_attendance, get_all_attendance, ensure_user_table, create_user, get_user_by_username, get_user_by_id, get_all_users, delete_user, get_attendance_for_name, get_today_attendance_count)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "local-demo-change-this-key-before-deployment")

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# --- Simple hardcoded admin account ---
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = "scrypt:32768:8:1$vh77OL314GVlUTsE$17c8f4d6d45b96d6342f9e421e92deb2a3e13872f0e3d4794a3b9cff6bb421c8dd4fc96403305cbc705ae43a644dd873a22240ca12f9407b43fe74038a1cd4bd"

class AdminUser(UserMixin):
    id = "admin"

class PortalUser(UserMixin):
    def __init__(self, row):
        self.id = "user:" + str(row["id"])
        self.name = row["name"]
        self.username = row["username"]
        self.role = "user"

@login_manager.user_loader
def load_user(user_id):
    if user_id == "admin":
        return AdminUser()
    if user_id and user_id.startswith("user:"):
        row = get_user_by_id(user_id.split(":", 1)[1])
        return PortalUser(row) if row else None
    return None

def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if current_user.get_id() != "admin":
            abort(403)
        return view(*args, **kwargs)
    return wrapped

def user_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if not current_user.get_id().startswith("user:"):
            abort(403)
        return view(*args, **kwargs)
    return wrapped

# --- Face recognition setup (same as before) ---
KNOWN_FACES_DIR = "known_faces"
EAR_THRESHOLD = 0.21

def load_known_faces():
    known_encodings = []
    known_names = []
    for filename in os.listdir(KNOWN_FACES_DIR):
        if filename.lower().endswith((".jpg", ".jpeg", ".png")):
            path = os.path.join(KNOWN_FACES_DIR, filename)
            image = face_recognition.load_image_file(path)
            encodings = face_recognition.face_encodings(image)
            if len(encodings) == 0:
                continue
            known_encodings.append(encodings[0])
            known_names.append(os.path.splitext(filename)[0])
    return known_encodings, known_names

def euclidean(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

def eye_aspect_ratio(eye_points):
    vertical1 = euclidean(eye_points[1], eye_points[5])
    vertical2 = euclidean(eye_points[2], eye_points[4])
    horizontal = euclidean(eye_points[0], eye_points[3])
    return (vertical1 + vertical2) / (2.0 * horizontal)

init_db()
ensure_user_table()
known_encodings, known_names = load_known_faces()
print(f"Loaded {len(known_names)} known face(s): {known_names}")

session_state = {}


# --- PUBLIC KIOSK PAGE (no login needed) ---
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/process_frame", methods=["POST"])
def process_frame():
    data = request.json
    image_data = data["image"].split(",")[1]
    img_bytes = base64.b64decode(image_data)
    np_arr = np.frombuffer(img_bytes, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    face_locations = face_recognition.face_locations(rgb)
    face_encodings = face_recognition.face_encodings(rgb, face_locations)

    results = []
    for encoding in face_encodings:
        distances = face_recognition.face_distance(known_encodings, encoding)
        name = "Unknown"
        if len(distances) > 0:
            best_index = distances.argmin()
            if distances[best_index] < 0.6:
                name = known_names[best_index]
        results.append(name)

    is_blinking = False
    landmarks_list = face_recognition.face_landmarks(rgb)
    if landmarks_list:
        landmarks = landmarks_list[0]
        left_ear = eye_aspect_ratio(landmarks['left_eye'])
        right_ear = eye_aspect_ratio(landmarks['right_eye'])
        avg_ear = (left_ear + right_ear) / 2.0
        if avg_ear < EAR_THRESHOLD:
            is_blinking = True

    marked = []
    for name in results:
        if name != "Unknown":
            key = name
            if key not in session_state:
                session_state[key] = {"blinked": False}
            if is_blinking:
                session_state[key]["blinked"] = True
            if session_state[key]["blinked"]:
                if mark_attendance(name):
                    marked.append(name)

    return jsonify({"names": results, "is_blinking": is_blinking, "marked": marked})


# --- LOGIN ---
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
            login_user(AdminUser())
            return redirect(url_for("admin_dashboard"))
        account = get_user_by_username(username or "")
        if account and check_password_hash(account["password_hash"], password or ""):
            login_user(PortalUser(account))
            return redirect(url_for("user_dashboard"))
        error = "Invalid username or password"
    return render_template("login.html", error=error)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


# --- ADMIN DASHBOARD (login required) ---
# --- ADMIN DASHBOARD (login required) ---
@app.route("/admin")
@admin_required
def admin_dashboard():
    records = get_all_attendance()
    return render_template("admin.html", records=records, users=get_all_users(), today_count=get_today_attendance_count())


@app.route("/admin/register", methods=["GET", "POST"])
@admin_required
def register():
    message = None
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        image_data = request.form.get("image")

        if not name or not image_data:
            message = "Name and photo are both required."
        else:
            img_bytes = base64.b64decode(image_data.split(",")[1])
            np_arr = np.frombuffer(img_bytes, np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            encodings = face_recognition.face_encodings(rgb)
            if len(encodings) == 0:
                message = "No face detected in the photo. Try again with a clearer shot."
            else:
                save_path = os.path.join(KNOWN_FACES_DIR, f"{name}.jpg")
                cv2.imwrite(save_path, frame)

                global known_encodings, known_names
                known_encodings, known_names = load_known_faces()

                message = f"✅ {name} registered successfully!"

    return render_template("register.html", message=message)
@app.route("/admin/people")
@admin_required
def people_list():
    people = []
    for filename in os.listdir(KNOWN_FACES_DIR):
        if filename.lower().endswith((".jpg", ".jpeg", ".png")):
            people.append(os.path.splitext(filename)[0])
    return render_template("people.html", people=people)


@app.route("/admin/people/delete/<name>", methods=["POST"])
@admin_required
def delete_person(name):
    for filename in os.listdir(KNOWN_FACES_DIR):
        if os.path.splitext(filename)[0] == name:
            os.remove(os.path.join(KNOWN_FACES_DIR, filename))

    global known_encodings, known_names
    known_encodings, known_names = load_known_faces()

    return redirect(url_for("people_list"))

@app.route("/admin/users", methods=["GET", "POST"])
@admin_required
def admin_users():
    message = None
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        name = request.form.get("name", "").strip()
        password = request.form.get("password", "")
        if not re.fullmatch(r"[a-z0-9._-]{3,32}", username):
            error = "Username must be 3–32 characters (letters, numbers, dot, underscore or hyphen)."
        elif not name or len(name) > 80:
            error = "Enter a valid registered person's name."
        elif len(password) < 8:
            error = "Password must contain at least 8 characters."
        elif name not in known_names:
            error = "Register this person's face first, using the exact same name."
        else:
            try:
                create_user(username, name, generate_password_hash(password))
                message = "Account created for " + name + "."
            except Exception:
                error = "That username or person already has an account."
    return render_template("admin_users.html", users=get_all_users(), message=message, error=error, people=known_names)


@app.route("/admin/users/delete/<int:user_id>", methods=["POST"])
@admin_required
def admin_delete_user(user_id):
    delete_user(user_id)
    return redirect(url_for("admin_users"))


@app.route("/user")
@user_required
def user_dashboard():
    records = get_attendance_for_name(current_user.name)
    today = __import__("datetime").datetime.now().strftime("%Y-%m-%d")
    present_days = len({row[2][:10] for row in records})
    today_present = any(row[2].startswith(today) for row in records)
    return render_template("user_dashboard.html", records=records[:10],
                           total_days=present_days, today_present=today_present,
                           person_name=current_user.name)


@app.route("/user/attendance")
@user_required
def user_attendance():
    records = get_attendance_for_name(current_user.name)
    return render_template("user_attendance.html", records=records, person_name=current_user.name)


@app.errorhandler(403)
def forbidden(_error):
    return render_template("forbidden.html"), 403


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)