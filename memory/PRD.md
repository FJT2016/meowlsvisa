# Meowls e-Visa Portal — PRD

## Problem Statement
Visa application for fake country "Meowls" similar to India e-visa:
- Users register, apply for a visa, upload passport + photo, track applications
- Admin portal for government officials to approve / reject visas
- AI-generated visa documents (with applicant photo embedded) emailed on approval
- Rejection emails sent on rejection
- All notifications go to applicant + full admin list simultaneously
- "Apply for Passport" button externally links to https://passport-meowl-apply.base44.app

## Tech Stack
- Frontend: React, Tailwind CSS, React Router, Sonner toasts
- Backend: FastAPI, Motor (MongoDB), bcrypt, session-cookie auth
- Integrations: OpenAI GPT-4o (document text), Resend (email), ReportLab (PDF)

## Current Admin List (password: `admin123` for all)
1. Fardaan Tareen — Fardaan.tareen@gmail.com
2. F Tareen — ftareen@dohacollege.com.qa  ← Resend account owner
3. S Almadani — salmadani@dohacollege.com.qa
4. M Alfaarizqi — malfaarizqi@dohacollege.com.qa
5. M Mehdi — mmehdi@dohacollege.com.qa
6. AD Faheem — adfaheem@dohacollege.com.qa

## Implemented (as of Apr 30, 2026)
- Full visa apply flow (5 steps: type, personal, travel, docs, review)
- Admin dashboard + review with approve/reject
- AI-generated visa PDF with applicant photo embedded
- Resend email (approval PDF + rejection) sent per-recipient with failure logging
- Removed `vnovruz@dohacollege.com.qa` from admins (DB + docs)
- Added "Apply for Passport" button (Home hero + Navbar) linking to
  https://passport-meowl-apply.base44.app (new tab)

## Known Limitation — Resend Sandbox (Apr 30, 2026)
- `SENDER_EMAIL=onboarding@resend.dev` + unverified domain
- Resend only allows sending to the account owner (`ftareen@dohacollege.com.qa`)
- All other recipients (applicants + other admins) return:
  "You can only send testing emails to your own email address..."
- Backend now sends **one email per recipient** so ftareen still reliably gets it,
  and each failure is logged individually (visible in `/var/log/supervisor/backend.err.log`)
- **User action needed**: verify a domain at https://resend.com/domains and update
  `SENDER_EMAIL` in `/app/backend/.env` (e.g. `noreply@yourdomain.com`) for every
  applicant + admin to actually receive emails.

## Backlog
- P1: Admin Dashboard pagination / search
- P2: Refactor `server.py` — split OpenAI + Resend + PDF into service modules
- P2: Email retry queue for transient Resend failures

## Files of Reference
- `/app/backend/server.py` — all routes, auth, AI, PDF, email
- `/app/frontend/src/pages/ApplyVisa.js` — applicant form (captures email)
- `/app/frontend/src/pages/AdminReview.js` — approve/reject trigger
- `/app/frontend/src/pages/Home.js` — Apply for Passport CTA
- `/app/frontend/src/components/Navbar.js` — Apply for Passport nav link
- `/app/ADMIN_CREDENTIALS.md` — admin list
