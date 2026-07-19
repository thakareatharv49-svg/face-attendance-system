import face_recognition
import cv2
import os
import math
from database import init_db, mark_attendance

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
                print(f"Warning: no face found in {filename}, skipping.")
                continue

            known_encodings.append(encodings[0])
            name = os.path.splitext(filename)[0]
            known_names.append(name)

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

cap = cv2.VideoCapture(0)

frame_count = 0
face_locations = []
face_names = []

# Track blink state and liveness per recognized name (resets each run)
consecutive_low = 0
live_confirmed = set()   # names that have blinked at least once this session
announced = set()

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame_count += 1

    if frame_count % 3 == 0:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Recognition (on downscaled frame for speed)
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_small)
        face_encodings = face_recognition.face_encodings(rgb_small, face_locations)

        face_names = []
        for face_encoding in face_encodings:
            distances = face_recognition.face_distance(known_encodings, face_encoding)
            name = "Unknown"
            if len(distances) > 0:
                best_index = distances.argmin()
                if distances[best_index] < 0.6:
                    name = known_names[best_index]
            face_names.append(name)

        # Blink detection (on full-res frame for accuracy)
        landmarks_list = face_recognition.face_landmarks(rgb)
        if landmarks_list:
            landmarks = landmarks_list[0]
            left_ear = eye_aspect_ratio(landmarks['left_eye'])
            right_ear = eye_aspect_ratio(landmarks['right_eye'])
            avg_ear = (left_ear + right_ear) / 2.0

            if avg_ear < EAR_THRESHOLD:
                consecutive_low += 1
            else:
                if consecutive_low >= 1 and face_names:
                    # A blink just completed - mark whoever is currently recognized as "live"
                    for name in face_names:
                        if name != "Unknown":
                            live_confirmed.add(name)
                consecutive_low = 0

        # Mark attendance only for people confirmed live via blink
        for name in face_names:
            if name != "Unknown" and name in live_confirmed:
                newly_marked = mark_attendance(name)
                if newly_marked and name not in announced:
                    print(f"✅ Attendance marked for {name} (liveness confirmed)")
                    announced.add(name)

    for (top, right, bottom, left), name in zip(face_locations, face_names):
        top *= 4
        right *= 4
        bottom *= 4
        left *= 4

        if name == "Unknown":
            color = (0, 0, 255)
            label = name
        elif name in live_confirmed:
            color = (0, 255, 0)
            label = f"{name} (live)"
        else:
            color = (0, 255, 255)
            label = f"{name} (blink to confirm)"

        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
        cv2.putText(frame, label, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

    cv2.imshow("Attendance System - press q to quit", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()