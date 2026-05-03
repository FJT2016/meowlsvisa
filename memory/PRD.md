# Meowls e-Visa Portal — PRD

## Problem Statement
Visa application for fake country "Meowls" similar to India e-visa:
- Users register, apply for a visa, upload passport + photo, track applications
- Admin portal for government officials to approve / reject visas
- AI-generated visa documents (with applicant photo embedded)
- **Device push notifications** (Web Push API + VAPID) for approve/reject
- **In-app PDF download** for approved visas
- **In-app rejection notice** with admin's reason
- **Full PWA support** — installable, offline app shell, service worker
- Email notifications (currently limited to Resend sandbox account owner)
- "Apply for Passport" button → https://passport-meowl-apply.base44.app

## Tech Stack
- Frontend: React, Tailwind, React Router, Sonner toasts, **PWA (manifest + service worker)**
- Backend: FastAPI, Motor (MongoDB), bcrypt sessions, **pywebpush + VAPID**
- Integrations: OpenAI GPT-4o (document text), Resend (email), ReportLab (PDF)

## Current Admin List (password: `admin123`)
1. Fardaan Tareen — Fardaan.tareen@gmail.com
2. F Tareen — ftareen@dohacollege.com.qa  ← Resend account owner
3. S Almadani — salmadani@dohacollege.com.qa
4. M Alfaarizqi — malfaarizqi@dohacollege.com.qa
5. M Mehdi — mmehdi@dohacollege.com.qa
6. AD Faheem — adfaheem@dohacollege.com.qa

## Implemented (as of May 3, 2026)
### Core flows
- Full visa apply flow (5 steps)
- Admin dashboard + review (approve / reject with admin_notes)
- AI-generated visa PDF with applicant photo embedded
- Resend per-recipient email (applicant + every admin, with individual failure logging)

### New in latest release
- **Push notifications** — `/api/push/vapid-public-key`, `/api/push/subscribe`,
  `/api/push/unsubscribe`; VAPID keys stored in `.env`; push sent on status change.
- **In-app notifications** — `/api/notifications` (unread approved/rejected),
  `/api/notifications/{id}/read`; toast shown on Dashboard mount.
- **In-app PDF download** — `/api/applications/{id}/visa-pdf` returns the PDF for
  the owner/admin; PDF is persisted (base64) when admin approves, generated on-demand
  if missing (for pre-existing approved apps).
- **Rejection in-app card** — red card on Application Details page with the
  admin's reason.
- **Full PWA** — manifest.json, icons (192/512 + Apple), service worker at `/sw.js`,
  push + notificationclick handlers, offline app-shell cache.
- **Apply for Passport** button on Home + Navbar → external Base44 passport app.

## Known Limitation — Resend Sandbox
- `SENDER_EMAIL=onboarding@resend.dev` (no verified domain)
- Resend only delivers to `ftareen@dohacollege.com.qa`; other recipients get
  "You can only send testing emails to your own email address..."
- Backend logs each failure individually; **in-app notifications + PDF download
  + push notifications are the primary delivery channel right now.**
- To enable email for everyone: verify a real domain at https://resend.com/domains,
  update `SENDER_EMAIL` in `/app/backend/.env`, restart backend.

## Backlog
- P1: Admin Dashboard pagination / search
- P2: Refactor `server.py` — split OpenAI + Resend + PDF into service modules
- P2: Move OpenAI PDF generation off the admin status PUT path into a background task
- P3: Email retry queue for transient Resend failures

## Key Files
- `/app/backend/server.py`
- `/app/backend/tests/test_push_pdf_notifications.py` (17 tests, all passing)
- `/app/frontend/src/pages/Dashboard.js`
- `/app/frontend/src/pages/ApplicationDetails.js`
- `/app/frontend/src/lib/pushNotifications.js`
- `/app/frontend/public/sw.js`
- `/app/frontend/public/manifest.json`
- `/app/frontend/public/index.html`
