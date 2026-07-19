import face_recognition

# Load the known reference photo
known_image = face_recognition.load_image_file("person1.jpg")
known_encoding = face_recognition.face_encodings(known_image)[0]

# Load the new test photo
test_image = face_recognition.load_image_file("person1_test.jpg")
test_encodings = face_recognition.face_encodings(test_image)

if len(test_encodings) == 0:
    print("No face found in test image!")
else:
    test_encoding = test_encodings[0]

    # Compare
    distance = face_recognition.face_distance([known_encoding], test_encoding)[0]
    match = face_recognition.compare_faces([known_encoding], test_encoding, tolerance=0.6)[0]

    print(f"Distance: {distance:.4f}")
    print(f"Match: {match}")