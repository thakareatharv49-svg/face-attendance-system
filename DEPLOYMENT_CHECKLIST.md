# Live submission checklist

## Before deploying
- [ ] Merge the release-readiness pull request into main after CI passes.
- [ ] Create a Render web service from the repository Blueprint.
- [ ] Confirm Python 3.11 is selected.
- [ ] Attach persistent storage mounted at /var/data.
- [ ] Set ADMIN_PASSWORD_HASH to a generated Werkzeug hash (never plaintext).
- [ ] Confirm SECRET_KEY is generated and COOKIE_SECURE is true.
- [ ] Confirm DATABASE_PATH=/var/data/attendance.db.
- [ ] Confirm KNOWN_FACES_DIR=/var/data/known_faces.
- [ ] Deploy and wait for the build to finish.

## After deployment
- [ ] Open /health and verify status is ok.
- [ ] Open /login and verify invalid credentials are rejected.
- [ ] Sign in with the configured admin credentials.
- [ ] Register one test person using the HTTPS camera page.
- [ ] Confirm the person appears in Manage people.
- [ ] Test kiosk recognition and blink check with that person.
- [ ] Confirm the dashboard records attendance.
- [ ] Confirm a second check-in on the same day is rejected as already marked.
- [ ] Export CSV and verify the downloaded records.
- [ ] Remove the test person and clean test attendance data if required.
- [ ] Verify the service URL works from the presentation device/network.

## Important
Do not use ephemeral storage for a real demonstration with saved registrations. An ephemeral host can erase both the face image directory and SQLite database during a deploy or restart. Face recognition depends on native dlib build support; if the host build fails, use a Python 3.11 host with CMake and a C++ compiler.
