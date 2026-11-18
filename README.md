# AttendAI — AI Face Recognition Attendance System

A Flask attendance kiosk using face recognition and a blink-based liveness prompt, with a protected admin dashboard, person registration, daily attendance records, and CSV export.

## Features
- Browser camera kiosk (HTTPS required when deployed)
- Face matching against registered face images
- One-person-at-a-time kiosk flow
- Fresh close-and-open blink check before check-in (basic liveness only)
- Atomic one-attendance-per-person-per-day SQLite writes
- Admin sign-in, registration, people removal, date/name filters, dashboard statistics, and CSV export
- CSRF protection, session cookie controls, request-size validation, input validation, login throttling, and security headers
- /health endpoint for hosting health checks

## Local setup (Windows PowerShell)

Use Python 3.11. Create and activate a virtual environment:
```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
Copy-Item .env.example .env
```

Generate a password hash:
```powershell
python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('Use-A-Long-Unique-Password'))"
```

Put the generated value in ADMIN_PASSWORD_HASH in .env. Set SECRET_KEY to a long random value and APP_TIMEZONE to your local timezone (the deployment Blueprint defaults to Asia/Kolkata). Never commit a real .env file or credentials.

Start the server:
```powershell
python app.py
```

Open the kiosk at http://127.0.0.1:5000/, admin at http://127.0.0.1:5000/login, and health at http://127.0.0.1:5000/health.

## Deployment

A Render Blueprint is included in render.yaml. Create a Render web service from this repository and configure the generated admin password hash in its environment settings. Use Python 3.11, keep COOKIE_SECURE=true, and attach persistent storage mounted at /var/data. The database and registered face photos must survive restarts and deployments. The Blueprint uses a paid service/disk configuration because free instances do not provide persistent local storage.

After deployment, verify the HTTPS /health endpoint returns status ok, then test admin login, registration, kiosk recognition, same-day duplicate prevention, and CSV export. The deployed site must use HTTPS because browsers restrict camera access on insecure origins.

Do not deploy with an ephemeral filesystem for real attendance: SQLite records and registered face photos may be lost. For multiple application instances, move persistence to shared PostgreSQL and liveness state to shared Redis before scaling horizontally.

## Tests
```powershell
pytest -q
```

## Biometric privacy and limitations

Face images are sensitive biometric data. Obtain clear consent, provide an alternative attendance method, restrict admin access, define a retention/deletion policy, and comply with applicable privacy and workplace/education rules. Blink detection is a basic liveness signal only; it does not reliably defeat replay videos, masks, or advanced presentation attacks. Do not use this as the sole basis for high-stakes decisions.

## Troubleshooting
- Camera does not open: use localhost or HTTPS, allow camera permission, and reload.
- Face not recognized: register one clear, front-facing image per person with adequate lighting.
- dlib build fails: use Python 3.11 and a host with CMake, a C++ compiler, and native numerical libraries.
- Data disappears after deployment: configure persistent storage and point DATABASE_PATH and KNOWN_FACES_DIR to it.