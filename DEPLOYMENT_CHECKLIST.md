# Live submission checklist — free hybrid setup

## Before deployment
- [ ] Merge the release-readiness pull request after CI passes.
- [ ] Import the GitHub repository into Vercel on the Hobby plan.
- [ ] Confirm the intended use is allowed under Vercel Hobby's current personal/non-commercial terms.
- [ ] Install Python 3.11 and Cloudflare Tunnel on the Windows PC.
- [ ] Configure .env with a long SECRET_KEY and ADMIN_PASSWORD_HASH.
- [ ] Install dependencies with pip install -r requirements.txt.
- [ ] Start the backend and Cloudflare Quick Tunnel with scripts/start-hybrid.ps1.
- [ ] Copy the current trycloudflare.com URL into vercel.json using scripts/set-vercel-backend.ps1.
- [ ] Commit and push vercel.json so Vercel deploys the reverse proxy.

## After deployment
- [ ] Open the Vercel HTTPS URL and verify /health returns status ok.
- [ ] Verify the kiosk camera permission prompt works.
- [ ] Sign in to /login with the configured admin credentials.
- [ ] Register one test person using the HTTPS camera page.
- [ ] Confirm the person appears in Manage people.
- [ ] Test kiosk recognition and blink check with that person.
- [ ] Confirm the dashboard records attendance.
- [ ] Confirm a second check-in on the same day is rejected as already marked.
- [ ] Export CSV and verify the downloaded records.
- [ ] Remove the test person and clean test attendance data if required.
- [ ] Verify the Vercel URL works from the presentation device/network.

## Keep it online during the demo

- [ ] Keep the Windows PC awake and connected to the internet.
- [ ] Keep the Flask and cloudflared processes running.
- [ ] Back up the SQLite database and known_faces directory.
- [ ] Do not restart the Quick Tunnel after deploying Vercel unless you update vercel.json and redeploy.
- [ ] Share the Vercel URL, not the temporary Cloudflare tunnel URL.

## Limitations

The free hybrid setup has no uptime guarantee. The app is unavailable when the PC or tunnel is offline. Quick Tunnel hostnames are temporary. SQLite and face images remain on the local PC. This is suitable for a controlled demonstration, not long-term institutional production attendance. Blink detection is basic liveness only, not certified anti-spoofing.
