# Free hybrid deployment (Vercel static page + local AI backend)

This setup keeps Flask, face recognition, SQLite, and registered face images on the Windows PC. Vercel Hobby hosts a static launch page. Cloudflare Quick Tunnel exposes the existing Flask app directly over HTTPS.

**Hosting cost: $0**, using Vercel Hobby and Cloudflare Quick Tunnel. This is a demo setup, not an always-on production service.

Vercel Hobby is intended for personal, non-commercial use. Vercel's fair-use guidelines also exclude using its platform as a proxy, so this design deliberately does not proxy backend traffic through Vercel.

## Architecture

Vercel static launch page -> user clicks Launch AttendAI -> Cloudflare Quick Tunnel HTTPS URL -> Flask on this PC -> face_recognition/OpenCV + local SQLite and known_faces/

The Vercel URL is a small project landing page. The actual attendance kiosk and admin dashboard open on the Cloudflare HTTPS URL. Camera permission is supported on that HTTPS origin. The backend and data remain on the PC.

## One-time setup

1. Import this GitHub repository into Vercel and keep the Hobby plan.
2. Vercel should deploy the static output from the public directory using vercel.json. It does not host the Python backend.
3. Install Python 3.11 and Cloudflare Tunnel on Windows:
   ~~~powershell
   winget install --id Cloudflare.cloudflared
   ~~~
4. At the repository root, create the environment and install dependencies:
   ~~~powershell
   py -3.11 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install --upgrade pip wheel
   pip install -r requirements.txt
   Copy-Item .env.example .env
   ~~~
5. Edit .env. Set a long random SECRET_KEY and generated ADMIN_PASSWORD_HASH.
6. Start the backend and tunnel:
   ~~~powershell
   .\scripts\start-hybrid.ps1
   ~~~
7. Copy the HTTPS trycloudflare.com URL printed by cloudflared. In a second PowerShell window, run:
   ~~~powershell
   .\scripts\set-vercel-backend.ps1 -TunnelUrl "https://YOUR-REAL-NAME.trycloudflare.com"
   git add public/config.js
   git commit -m "Update AttendAI launch URL"
   git push
   ~~~
8. Vercel redeploys the static launch page. Open its URL and click Open AttendAI attendance. The actual app should open on the Cloudflare HTTPS URL.
9. Test /health, camera permission, registration, recognition, attendance, admin login, and CSV export on the Cloudflare app URL.

## Important operating rules

- Keep the Windows PC, Flask process, internet connection, and Cloudflare tunnel terminal running for the whole demo.
- Quick Tunnel hostnames are random and temporary. If the tunnel stops or restarts, it receives a new hostname. Repeat steps 6-7 and wait for Vercel to redeploy.
- SQLite and registered face photos remain on this PC. Back up the database and known_faces/ directory before the presentation.
- Do not share the admin password publicly. The Cloudflare URL is the public app URL; protect the admin area with a strong password.
- Vercel hosts only the static landing page. Browser requests to the Flask application go directly to Cloudflare, not through Vercel.
- If the PC sleeps, shuts down, loses internet, or the tunnel exits, the attendance app becomes unavailable.
- Do not use this temporary demo architecture for institutional attendance or sensitive long-term records without an always-on host, durable backups, consent, retention controls, and a security review.

## Troubleshooting

- Vercel page does not show a launch button: confirm public/config.js contains the current tunnel URL and the latest Vercel deployment finished.
- Cloudflare app returns an error: check Flask and cloudflared are running.
- Camera is blocked: open the Cloudflare HTTPS app URL, allow camera permission, and reload.
- Admin login fails: verify the configured username and password hash in .env.
- Face recognition fails locally: check backend-error.log, Python 3.11, dlib installation, and camera lighting.
