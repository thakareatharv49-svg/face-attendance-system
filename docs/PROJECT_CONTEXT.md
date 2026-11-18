# Project Context Snapshot — 2026-11-18

## Repository
- GitHub: https://github.com/thakareatharv49-svg/face-attendance-system
- Default branch observed in the project workflow: `main`
- Local Windows working directory: `%USERPROFILE%\face-attendance`

## Product
AI Face Attendance is a Flask web application using Python, OpenCV, face_recognition/dlib, and SQLite. It provides:
- A role-selection/home page with Admin Login and User Login
- Admin portal for managing people, accounts, and attendance reports
- Personal user dashboard and attendance history
- A dedicated browser-based attendance kiosk
- Face recognition and blink-based liveness verification
- SQLite attendance records

## Confirmed working behavior
- Local Flask application has previously run at `http://127.0.0.1:5000`.
- Webcam capture, face recognition, and eye-landmark processing were tested locally.
- The kiosk confirmation logic was updated so an existing attendance record for the current date is returned as `already_marked` before another blink is required.
- The user confirmed that the “already marked” / attendance confirmation issue was fixed.
- The kiosk page was redesigned while retaining the existing JavaScript element IDs and backend endpoint integration. The user has not yet explicitly confirmed the final visual result.

## Local runtime
- Windows + PowerShell
- Python virtual environment: `venv`
- Flask server should bind to `127.0.0.1:5000` with debug mode disabled for the current tunnel demo.
- Cloudflared version installed: `2026.11.1`
- Executable observed at: `C:\Program Files (x86)\cloudflared\cloudflared.exe`

## Temporary public demo
A Cloudflare Quick Tunnel was created successfully on 2026-11-18. Quick Tunnel URLs are ephemeral and must not be treated as permanent project configuration. The currently generated URL may stop working when the tunnel process exits or be replaced on restart. Do not store temporary tunnel URLs in source code, README, or committed configuration.

To start a fresh temporary tunnel (while Flask is already listening on port 5000), run in a separate PowerShell window:
```powershell
& "C:\Program Files (x86)\cloudflared\cloudflared.exe" tunnel --url http://127.0.0.1:5000
```
Keep both the Flask server and cloudflared processes running. If the tunnel reports 502, first verify that Flask is reachable at `http://127.0.0.1:5000/`. Error 1033 on an old Quick Tunnel URL means that tunnel is no longer available; use the new URL printed by cloudflared.

## Admin credentials and secrets
- Admin username used during the demo: `admin`.
- The Admin password was reset during the 2026-11-18 session. The password itself is intentionally not recorded here.
- Generate the admin password hash in the process environment **before importing** the Flask app, because authentication configuration may be read during module import.
- Never commit plaintext passwords, password hashes, Flask secret keys, session cookies, API tokens, or other secrets.
- Use a persistent, high-entropy `FLASK_SECRET_KEY` for a stable deployment. Do not generate a new key on every production restart.
- The user has not yet explicitly confirmed a successful Admin dashboard login after the latest reset.

## Data that must be preserved
- `attendance.db` contains attendance records and must not be deleted or reset.
- Registered face images in `known_faces/` must be preserved.
- Do not run destructive cleanup commands such as `git clean` or broad wildcard deletion.
- Back up the SQLite database and registered face images before migrations or deployment changes.

## Deployment status and limitations
- The current public demo is a Quick Tunnel forwarding to a Flask server running on the user's Windows computer. It is not permanent hosting.
- The computer, Flask process, network connection, and tunnel process must remain available.
- Anyone with the temporary URL can reach the public-facing app; share only for controlled testing. Do not expose real attendance/biometric data until authentication, authorization, CSRF/session handling, rate limiting, and data protection have been reviewed.
- The current Flask development server is not a production deployment architecture. Before a public launch, use a production WSGI server, persistent secure configuration, HTTPS-aware proxy/session settings, durable storage/backups, and a deployment platform appropriate for the webcam/biometric workflow.

## Known local Git working-tree caution
At the last local status report (2026-11-18), `app.py` and `templates/index.html` had uncommitted modifications. Several backup files and strangely named untracked files were also present. Those local changes have **not been verified as committed or pushed** by this snapshot. Review the diffs and untracked filenames carefully; do not use `git add .`, `git clean`, or wildcard deletion. Preserve the source modifications that contain the attendance fix and kiosk redesign, and selectively stage only reviewed project files.

## Next actions
1. Confirm the latest Admin login succeeds.
2. Test Admin Login, User Login, kiosk recognition, blink confirmation, and already-marked behavior through HTTPS from a second device.
3. Review and selectively commit the local `app.py` and `templates/index.html` changes after checking their diffs.
4. Clean up accidental backup/garbled untracked files only after identifying each exact file; do not delete database or face data.
5. Add a documented production deployment plan and complete a security review before making the service publicly available.
6. Replace the temporary Quick Tunnel with a stable deployment and persistent domain/hosting when ready.
