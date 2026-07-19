import face_recognition

image = face_recognition.load_image_file("person1.jpg")
encodings = face_recognition.face_encodings(image)

if len(encodings) == 0:
    print("No face found in the image!")
else:
    encoding = encodings[0]
    print("Face found! Embedding vector:")
    print(encoding)
    print("\nVector length:", len(encoding))