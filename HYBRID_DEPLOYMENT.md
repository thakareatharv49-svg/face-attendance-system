# Free hybrid deployment (Vercel + local AI backend)

This setup keeps Flask, face recognition, SQLite, and registered face images on the Windows PC. Vercel is the public HTTPS reverse-proxy front door. Cloudflare Quick Tunnel connects Vercel to the local Flask server.

**Hosting cost: $0**, using Vercel Hobby and Cloudflare Quick Tunnel. This is a demo setup, not an always-on production service.

## Architecture

Browser -> Vercel HTTPS URL -> Vercel external rewrite -> Cloudflare Quick Tunnel -> Flask on this PC -> face_recognition/OpenCV + local SQLite and known_faces/

The Vercel URL is the URL to share. The browser remains on HTTPS, so camera permission is available. The backend and data remain on the PC.

## One-time setup

1. Import this GitHub repository into Vercel and select release/production-readiness for an initial preview, or main after the release PR is merged.
2. Keep the Vercel project on the Hobby plan. Hobby is intended for personal, non-commercial use; confirm your intended use complies with Vercel's current terms.
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
5. Edit .env. Set a long random SECRET_KEY and generated ADMIN_PASSWORD_HASH. The hybrid launcher sets COOKIE_SECURE=true for HTTPS access.
6. Start the backend and tunnel:
   ~~~powershell
   .\scripts\start-hybrid.ps1
   ~~~
7. Copy the HTTPS trycloudflare.com URL printed by cloudflared. In a second PowerShell window, run:
   ~~~powershell
   .\scripts\set-vercel-backend.ps1 -TunnelUrl "https://YOUR-REAL-NAME.trycloudflare.com"
   git add vercel.json
   git commit -m "Configure Vercel proxy for current demo tunnel"
   git push
   ~~~
8. Vercel deploys the updated vercel.json. Open the Vercel project URL and test /health, camera permission, registration, recognition, attendance, admin login, and CSV export.

## Important operating rules

- Keep the Windows PC, Flask process, internet connection, and Cloudflare tunnel terminal running for the whole demo.
- Quick Tunnel hostnames are random and temporary. If the tunnel stops or restarts, it receives a new hostname. Repeat steps 6-7 and wait for Vercel to redeploy.
- SQLite and registered face photos remain on this PC. Back up the database and known_faces/ directory before the presentation.
- Do not share the temporary Cloudflare origin URL or admin password publicly. Share only the Vercel URL.
- Vercel is a reverse proxy, not a separate static frontend. All application routes and static assets are served by Flask through the proxy.
- If the PC sleeps, shuts down, loses internet, or the tunnel exits, the public app becomes unavailable.
- Do not use this temporary demo architecture for institutional attendance or sensitive long-term records without an always-on host, durable backups, consent, retention controls, and a security review.

## Troubleshooting

- Vercel returns 502/504: check Flask and cloudflared are running and vercel.json targets the current tunnel URL.
- Camera is blocked: open the Vercel HTTPS URL, allow camera permission, and reload.
- Admin POST fails: verify the Vercel proxy points to the active tunnel and clear stale site cookies.
- Face recognition fails locally: check backend-error.log, Python 3.11, dlib installation, and camera lighting.
