# Meowls e-Visa Portal — PRD

## Problem Statement
Visa application for fake country "Meowls":
- Users register, apply, upload passport + photo, track applications
- Admin portal (government officials) approves / rejects visas
- AI-generated visa documents (with applicant photo) + in-app PDF download
- Push + in-app + email notifications for approve/reject
- Full PWA (installable, offline, service worker)
- "Apply for Passport" button → https://passport-meowl-apply.base44.app

## Tech Stack
- Frontend: React, Tailwind, React Router, Sonner, PWA (manifest + service worker)
- Backend: FastAPI, Motor, bcrypt sessions, pywebpush + VAPID, resend, reportlab, OpenAI (gpt-4o)

## Backend module layout (post-refactor May 4, 2026)
```
backend/
  server.py              # thin wire-up + startup hook (email retry worker)
  config.py              # env + constants
  database.py            # Mongo client + db
  models.py              # Pydantic models
  services/
    auth.py              # hash, verify, get_current_user
    pdf.py               # AI text + PDF renderer + background persistence
    email.py             # send_approval/rejection + retry queue + retry worker
    push.py              # send_push_to_user (VAPID)
  routes/
    auth.py              # /auth/*
    applications.py      # /applications/*
    admin.py             # /admin/applications (paginated)
    notifications.py     # /notifications/*, /applications/{id}/visa-pdf
    push.py              # /push/*
  tests/
    test_push_pdf_notifications.py  (17 passing)
```

## Admin List (password `admin123`)
1. Fardaan Tareen — Fardaan.tareen@gmail.com
2. F Tareen — ftareen@dohacollege.com.qa  ← Resend account owner
3. S Almadani — salmadani@dohacollege.com.qa
4. M Alfaarizqi — malfaarizqi@dohacollege.com.qa
5. M Mehdi — mmehdi@dohacollege.com.qa
6. AD Faheem — adfaheem@dohacollege.com.qa

## Implemented (as of May 4, 2026)
### Core flows
- Full visa apply flow (5 steps)
- Admin dashboard + review (approve/reject with admin_notes)
- AI-generated visa PDF with applicant photo embedded
- Resend per-recipient email (individual failure logging)
- Web push notifications (VAPID) on approve/reject
- In-app notifications (toast + persistent `status_seen_at`)
- In-app PDF download (persisted on approval, on-demand fallback)
- Rejection card with admin_notes
- Full PWA (manifest, sw.js, icons, offline shell)
- Install App banner (Chrome/Edge/Android + iOS Safari fallback)
- Apply for Passport external link

### New in latest release (refactor & scale)
- **Backend refactor** — `server.py` now just wires routers; all logic lives in
  `services/*` and `routes/*`. Clean separation by concern.
- **Background PDF generation** — admin `PUT /admin/applications/{id}/status=approved`
  returns immediately; PDF + email + push run as an async pipeline. On-demand
  fallback in `visa-pdf` endpoint covers the race window.
- **Server-side pagination** — `GET /api/admin/applications?page&page_size&status&search`
  returns `{items, total, page, page_size, total_pages}`; Mongo regex search across
  application_id, full_name, passport_number, email, nationality. Legacy flat-array
  response preserved when `page` omitted (backwards compat).
- **Email retry queue** — `db.email_retry_queue` collection. Non-permanent failures
  auto-retry with exponential backoff (1m, 5m, 15m, 1h, 6h; max 5 attempts).
  Permanent errors (Resend sandbox "verify a domain") are NOT retried.
  Background worker polls every 30s (started on FastAPI `startup` event).

## Known Limitation — Resend Sandbox
- Current key only delivers to `ftareen@dohacollege.com.qa`.
- The retry queue correctly classifies this as permanent and skips it (no spam).
- To fix: verify a domain at https://resend.com/domains; update `SENDER_EMAIL`.

## Backlog
- P2: Swap legacy flat-array admin endpoint for pagination-only once frontend
  is fully migrated (already migrated in `AdminDashboard.js`; pytest still covers legacy).
- P3: Metrics endpoint surfacing retry-queue depth, failed counts.
- P3: Rate-limit admin status updates so the background pipeline doesn't pile up.
