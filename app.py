from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import face_recognition
import numpy as np
import cv2
import os
import math
import base64
from database import init_db, mark_attendance, get_all_attendance

app = Flask(__name__)
app.secret_key = "change-this-secret-key-later"  # needed for login sessions

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# --- Simple hardcoded admin account ---
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

class AdminUser(UserMixin):
    id = "admin"

@login_manager.user_loader
def load_user(user_id):
    if user_id == "admin":
        return AdminUser()
    return None

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
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            login_user(AdminUser())
            return redirect(url_for("admin_dashboard"))
        else:
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
@login_required
def admin_dashboard():
    records = get_all_attendance()
    return render_template("admin.html", records=records)


@app.route("/admin/register", methods=["GET", "POST"])
@login_required
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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)