# 🎯 AI Face Recognition Attendance System

A face recognition-based attendance system with liveness detection (anti-spoofing), built with Python, OpenCV, face_recognition, and Flask.

## Features

- 🛡️ Separate role-protected admin and personal user dashboards
- 👤 Admin-managed user accounts linked to registered face identities
- 🔒 Password-hashed user credentials and per-user attendance history

- 🎥 Live face detection and recognition
- 👁️ Blink-based liveness detection (prevents photo spoofing)
- 📋 Automatic attendance logging with SQLite
- 🌐 Browser-based kiosk page — works from any device's camera
- 🔐 Admin login system
- ➕ Register new people via live camera (no manual file uploads)
- 👥 Admin panel to view and remove registered people

## Tech Stack

- Python
- OpenCV
- face_recognition (dlib-based)
- Flask + Flask-Login
- SQLite

## Setup

1. Clone the repository
2. Create a virtual environment
3. Install dependencies
4. Set a strong `FLASK_SECRET_KEY` environment variable before running the app
4. Run the app
5. Open in your browser
   - User/kiosk page: `http://localhost:5000/`
   - Sign-in: `http://localhost:5000/login` (admin and user accounts)
   - Admin dashboard: `http://localhost:5000/admin` (admin credentials are configured in `app.py`)
   - User dashboard: `http://localhost:5000/user` (accounts are created by the admin)

## How it works

1. Admin logs in and registers people via live camera capture
2. Users walk up to the kiosk page, camera recognizes their face
3. User blinks to confirm liveness (prevents someone using a photo)
4. Attendance is automatically logged with a timestamp

## Contributing

Contributions are welcome! Feel free to open an issue or submit a pull request.

## License

MIT License