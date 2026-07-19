import face_recognition
import os

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
            name = os.path.splitext(filename)[0]  # filename without extension
            known_names.append(name)

    return known_encodings, known_names


def recognize_face(test_image_path, known_encodings, known_names, tolerance=0.6):
    test_image = face_recognition.load_image_file(test_image_path)
    test_encodings = face_recognition.face_encodings(test_image)

    if len(test_encodings) == 0:
        print("No face found in test image.")
        return

    test_encoding = test_encodings[0]

    distances = face_recognition.face_distance(known_encodings, test_encoding)
    best_match_index = distances.argmin()
    best_distance = distances[best_match_index]

    if best_distance < tolerance:
        print(f"Match: {known_names[best_match_index]} (distance: {best_distance:.4f})")
    else:
        print(f"Unknown person (closest distance: {best_distance:.4f})")


if __name__ == "__main__":
    known_encodings, known_names = load_known_faces()
    print(f"Loaded {len(known_names)} known face(s): {known_names}")

    recognize_face("person1_test.jpg", known_encodings, known_names)