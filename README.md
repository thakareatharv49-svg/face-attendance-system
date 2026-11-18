# 🎯 AI Face Recognition Attendance System

A face recognition-based attendance system with liveness detection (anti-spoofing), built with Python, OpenCV, face_recognition, and Flask.

## Features

- 🛡️ Separate role-protected admin and personal user dashboards
- 👤 Admin-managed user accounts linked to registered face identities
- 🔒 Password-hashed user credentials, password changes and per-user attendance history
- 📊 Admin date-range reports and CSV export
- 🗓️ Personal attendance calendar and profile settings

- 🎥 Live face detection and recognition
- 👁️ Blink-based liveness check to help deter static-photo spoofing
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

1. Clone the repository.
2. Create and activate a Python virtual environment.
3. Install the project's Python dependencies (including Flask, Flask-Login, OpenCV, NumPy, face_recognition and dlib).
4. Set a persistent secret key before starting the app. In PowerShell: `$env:FLASK_SECRET_KEY = [guid]::NewGuid().ToString("N") + [guid]::NewGuid().ToString("N")`.
5. Start the app with `python app.py`.
6. Open in your browser.
   - User/kiosk page: `http://localhost:5000/`
   - Sign-in: `http://localhost:5000/login` (admin and user accounts)
   - Admin dashboard: `http://localhost:5000/admin` (configure credentials using the instructions below)
   - User dashboard: `http://localhost:5000/user` (accounts are created by the admin)

### Administrator credentials

You can set a known admin password without changing source code. In PowerShell, replace the example password with a strong private password, then start the app in the same terminal:

```powershell
$env:ADMIN_USERNAME = "admin"
$env:ADMIN_PASSWORD_HASH = & .\venv\Scripts\python.exe -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('Replace-With-A-Strong-Password'))"
```

Keep the generated hash in your environment configuration; never commit a plaintext password or hash to the repository.

### Account setup

- The administrator registers a person's face first under **People**.
- The administrator creates that person's username and temporary password under **User accounts**.
- The user signs in at `/login`; the app sends them to their personal dashboard.
- Users can view only attendance entries for their own registered name. Admin routes are role-protected.
- The kiosk remains available at `/`; it records attendance after a recognized face completes a blink transition.
- Set `FLASK_SECRET_KEY` to the same strong value on every restart. For HTTPS hosting, set `FLASK_HTTPS_ONLY=true`.

**Security note:** Do not expose the local Flask server through a public tunnel until the deployment configuration and admin credentials have been reviewed. Face images and SQLite data remain on the host machine.

## How it works

1. Admin logs in and registers people via live camera capture
2. Users walk up to the kiosk page, camera recognizes their face
3. User blinks to confirm liveness (prevents someone using a photo)
4. Attendance is automatically logged with a timestamp

## Contributing

Contributions are welcome! Feel free to open an issue or submit a pull request.

## License

MIT License