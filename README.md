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
~~~powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip wheel
pip install -r requirements.txt
Copy-Item .env.example .env
~~~

Generate an admin password hash:
~~~powershell
python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('Use-A-Long-Unique-Password'))"
~~~

Put the generated value in ADMIN_PASSWORD_HASH in .env. Set SECRET_KEY to a long random value and APP_TIMEZONE to your local timezone (Asia/Kolkata for this deployment). Never commit a real .env file or credentials.

Start locally with:
~~~powershell
python app.py
~~~

Open the kiosk at http://127.0.0.1:5000/, admin at http://127.0.0.1:5000/login, and health at http://127.0.0.1:5000/health.

## Free hybrid deployment (recommended for the college demo)

Use Vercel Hobby as the public HTTPS reverse-proxy front door and Cloudflare Quick Tunnel to connect it to the Flask backend running on your Windows PC. Face recognition, SQLite, and registered face images stay on your PC.

Follow **HYBRID_DEPLOYMENT.md** for the exact setup and PowerShell scripts.

Important limitations:
- The PC, backend process, internet connection, and tunnel must stay running during the demo.
- Cloudflare Quick Tunnel URLs are temporary and change when restarted; update vercel.json and redeploy Vercel whenever the URL changes.
- If the PC sleeps or the tunnel stops, the public website becomes unavailable.
- Vercel Hobby is intended for personal, non-commercial use; check its terms for your use case.
- This is a demo deployment, not a reliable always-on production host.

## Alternative deployment

A Render Blueprint is included in render.yaml, but it uses a paid service and persistent disk. It does not meet the zero-cost requirement. Do not create it for the free demo.

## Tests
~~~powershell
pytest -q
~~~

## Biometric privacy and limitations

Face images are sensitive biometric data. Obtain clear consent, provide an alternative attendance method, restrict admin access, define a retention/deletion policy, and comply with applicable privacy and workplace/education rules. Blink detection is a basic liveness signal only; it does not reliably defeat replay videos, masks, or advanced presentation attacks. Do not use this as the sole basis for high-stakes decisions.

## Troubleshooting
- Camera does not open: use localhost or HTTPS, allow camera permission, and reload.
- Face not recognized: register one clear, front-facing image per person with adequate lighting.
- dlib build fails: use Python 3.11 and a host with CMake, a C++ compiler, and native numerical libraries.
- Data disappears: in the free hybrid setup, data is stored locally on the Windows PC. Back up the database and known_faces directory.
