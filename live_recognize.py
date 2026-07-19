import face_recognition
import cv2
import os
from database import init_db, mark_attendance

KNOWN_FACES_DIR = "known_faces"

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


init_db()
known_encodings, known_names = load_known_faces()
print(f"Loaded {len(known_names)} known face(s): {known_names}")

cap = cv2.VideoCapture(0)

frame_count = 0
face_locations = []
face_names = []

# Track who we've already shown a "Marked present" message for, this session
announced = set()

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame_count += 1

    if frame_count % 5 == 0:
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        face_names = []
        for face_encoding in face_encodings:
            distances = face_recognition.face_distance(known_encodings, face_encoding)
            name = "Unknown"
            if len(distances) > 0:
                best_index = distances.argmin()
                if distances[best_index] < 0.6:
                    name = known_names[best_index]

            face_names.append(name)

            # Log attendance if it's a known person
            if name != "Unknown":
                newly_marked = mark_attendance(name)
                if newly_marked and name not in announced:
                    print(f"✅ Attendance marked for {name}")
                    announced.add(name)

    for (top, right, bottom, left), name in zip(face_locations, face_names):
        top *= 4
        right *= 4
        bottom *= 4
        left *= 4

        color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
        cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

    cv2.imshow("Attendance System - press q to quit", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()