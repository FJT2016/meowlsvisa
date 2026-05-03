"""
Tests for push notifications, in-app notifications, visa PDF download, and PWA.
"""
import os
import uuid
import time
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://meowls-visa.preview.emergentagent.com").rstrip("/")
ADMIN_EMAIL = "Fardaan.tareen@gmail.com"
ADMIN_PASSWORD = "admin123"


# ---------- helpers / fixtures ----------

@pytest.fixture(scope="module")
def admin_session():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert r.status_code == 200, f"Admin login failed: {r.status_code} {r.text}"
    assert s.cookies.get("session_token")
    return s


@pytest.fixture(scope="module")
def applicant_session():
    """Register a fresh applicant for these tests."""
    s = requests.Session()
    suffix = uuid.uuid4().hex[:8]
    email = f"TEST_applicant_{suffix}@example.com"
    password = "testpass123"
    r = s.post(f"{BASE_URL}/api/auth/register", json={
        "email": email, "password": password, "name": f"TEST Applicant {suffix}"
    })
    assert r.status_code == 200, f"Register failed: {r.status_code} {r.text}"
    s.user_email = email  # type: ignore
    return s


@pytest.fixture(scope="module")
def submitted_application(applicant_session):
    s = applicant_session
    payload = {
        "visa_type": "tourist",
        "personal_info": {
            "full_name": "TEST Applicant",
            "email": getattr(s, "user_email", "test@example.com"),
            "nationality": "Wonderland",
            "passport_number": f"P{uuid.uuid4().hex[:8].upper()}",
            "date_of_birth": "1990-01-01",
        },
        "travel_details": {
            "purpose": "Tourism",
            "arrival_date": "2026-06-01",
            "departure_date": "2026-06-15",
        },
    }
    r = s.post(f"{BASE_URL}/api/applications", json=payload)
    assert r.status_code == 200, r.text
    app_id = r.json()["application_id"]

    r2 = s.post(f"{BASE_URL}/api/applications/{app_id}/submit")
    assert r2.status_code == 200, r2.text
    return app_id


# ---------- VAPID public key ----------

class TestVapid:
    def test_vapid_public_key_no_auth(self):
        r = requests.get(f"{BASE_URL}/api/push/vapid-public-key")
        assert r.status_code == 200, r.text
        data = r.json()
        assert "public_key" in data
        assert isinstance(data["public_key"], str) and len(data["public_key"]) > 20


# ---------- Push subscribe / unsubscribe ----------

class TestPushSubscribe:
    fake_endpoint = f"https://fcm.googleapis.com/fcm/send/test-fake-{uuid.uuid4().hex[:10]}"
    fake_sub = {
        "endpoint": fake_endpoint,
        "keys": {"p256dh": "BFAKEKEYBFAKEKEYBFAKEKEY", "auth": "abcDEF123"},
    }

    def test_subscribe_requires_auth(self):
        r = requests.post(f"{BASE_URL}/api/push/subscribe", json=self.fake_sub)
        assert r.status_code == 401

    def test_subscribe_success(self, applicant_session):
        r = applicant_session.post(f"{BASE_URL}/api/push/subscribe", json=self.fake_sub)
        assert r.status_code == 200, r.text
        assert r.json().get("ok") is True

    def test_subscribe_idempotent_upsert(self, applicant_session):
        # second call with same endpoint should still succeed (upsert)
        r = applicant_session.post(f"{BASE_URL}/api/push/subscribe", json=self.fake_sub)
        assert r.status_code == 200

    def test_unsubscribe_success(self, applicant_session):
        r = applicant_session.post(f"{BASE_URL}/api/push/unsubscribe", json=self.fake_sub)
        assert r.status_code == 200
        assert r.json().get("ok") is True


# ---------- Notifications + Approve flow + PDF ----------

class TestApprovalFlow:
    def test_approve_persists_pdf_and_creates_notification(self, admin_session, applicant_session, submitted_application):
        app_id = submitted_application

        # Approve via admin
        r = admin_session.put(
            f"{BASE_URL}/api/admin/applications/{app_id}/status",
            json={"status": "approved", "notes": "Looks good"},
        )
        assert r.status_code == 200, r.text

        # Allow background tasks (PDF persistence happened inline before update)
        time.sleep(1)

        # Notifications endpoint for applicant should include this app
        r2 = applicant_session.get(f"{BASE_URL}/api/notifications")
        assert r2.status_code == 200
        body = r2.json()
        assert body["count"] >= 1
        ids = [n["application_id"] for n in body["unread"]]
        assert app_id in ids
        item = next(n for n in body["unread"] if n["application_id"] == app_id)
        assert item["status"] == "approved"

        # PDF download as owner
        r3 = applicant_session.get(f"{BASE_URL}/api/applications/{app_id}/visa-pdf")
        assert r3.status_code == 200, r3.text
        assert r3.headers.get("content-type", "").startswith("application/pdf")
        assert "attachment" in r3.headers.get("content-disposition", "").lower()
        assert r3.content[:4] == b"%PDF"

        # Mark notification read
        r4 = applicant_session.post(f"{BASE_URL}/api/notifications/{app_id}/read")
        assert r4.status_code == 200
        assert r4.json().get("ok") is True

        # Notifications now empty for this app
        r5 = applicant_session.get(f"{BASE_URL}/api/notifications")
        assert r5.status_code == 200
        ids2 = [n["application_id"] for n in r5.json()["unread"]]
        assert app_id not in ids2

    def test_visa_pdf_unauthenticated(self, submitted_application):
        # use a brand new requests (no cookie)
        r = requests.get(f"{BASE_URL}/api/applications/{submitted_application}/visa-pdf")
        assert r.status_code == 401

    def test_visa_pdf_other_user_forbidden(self, submitted_application):
        # another fresh applicant must not be able to download
        s = requests.Session()
        suffix = uuid.uuid4().hex[:6]
        s.post(f"{BASE_URL}/api/auth/register", json={
            "email": f"TEST_other_{suffix}@example.com",
            "password": "testpass123",
            "name": "Other"
        })
        r = s.get(f"{BASE_URL}/api/applications/{submitted_application}/visa-pdf")
        assert r.status_code == 403

    def test_mark_read_404_for_nonexistent(self, applicant_session):
        r = applicant_session.post(f"{BASE_URL}/api/notifications/app_doesnotexist123/read")
        assert r.status_code == 404


class TestRejectionFlow:
    def test_reject_creates_notification_with_admin_notes(self, admin_session, applicant_session):
        # create + submit a new application
        s = applicant_session
        r = s.post(f"{BASE_URL}/api/applications", json={
            "visa_type": "business",
            "personal_info": {
                "full_name": "TEST Reject", "email": getattr(s, "user_email"),
                "nationality": "X", "passport_number": f"R{uuid.uuid4().hex[:8].upper()}",
                "date_of_birth": "1990-01-01",
            },
            "travel_details": {"purpose": "Biz", "arrival_date": "2026-07-01", "departure_date": "2026-07-10"},
        })
        assert r.status_code == 200
        app_id = r.json()["application_id"]
        s.post(f"{BASE_URL}/api/applications/{app_id}/submit")

        rejection_reason = "Insufficient documentation provided."
        r2 = admin_session.put(
            f"{BASE_URL}/api/admin/applications/{app_id}/status",
            json={"status": "rejected", "notes": rejection_reason},
        )
        assert r2.status_code == 200

        time.sleep(0.5)

        r3 = s.get(f"{BASE_URL}/api/notifications")
        assert r3.status_code == 200
        item = next((n for n in r3.json()["unread"] if n["application_id"] == app_id), None)
        assert item is not None
        assert item["status"] == "rejected"
        assert item.get("admin_notes") == rejection_reason

        # PDF should NOT be downloadable for rejected
        r4 = s.get(f"{BASE_URL}/api/applications/{app_id}/visa-pdf")
        assert r4.status_code == 400


# ---------- Auth regressions / admin list ----------

class TestAuthRegression:
    def test_login_admin(self):
        r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
        assert r.status_code == 200

    def test_register_works(self):
        suffix = uuid.uuid4().hex[:8]
        r = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": f"TEST_reg_{suffix}@example.com",
            "password": "testpass123",
            "name": "Reg User"
        })
        assert r.status_code == 200

    def test_removed_admin_is_not_admin(self, admin_session):
        # Hit /admin/applications as removed user — they shouldn't be able to login as admin.
        # If the user still exists, login may succeed but role should not be admin.
        s = requests.Session()
        r = s.post(f"{BASE_URL}/api/auth/login", json={
            "email": "vnovruz@dohacollege.com.qa", "password": "admin123"
        })
        # Either invalid creds (deleted) or non-admin. Both acceptable; just must not be admin.
        if r.status_code == 200:
            r2 = s.get(f"{BASE_URL}/api/admin/applications")
            assert r2.status_code == 403, "vnovruz still has admin access"
        else:
            assert r.status_code == 401


# ---------- PWA static assets ----------

class TestPWAAssets:
    def test_manifest_served(self):
        r = requests.get(f"{BASE_URL}/manifest.json")
        assert r.status_code == 200
        assert "application/json" in r.headers.get("content-type", "") or r.text.strip().startswith("{")
        data = r.json()
        assert "name" in data or "short_name" in data
        assert "icons" in data

    def test_sw_served(self):
        r = requests.get(f"{BASE_URL}/sw.js")
        assert r.status_code == 200
        ct = r.headers.get("content-type", "")
        assert "javascript" in ct or "application/x-javascript" in ct, f"sw.js content-type: {ct}"
        assert "self.addEventListener" in r.text or "push" in r.text

    def test_icons_served(self):
        for path in ("/icon-192.png", "/icon-512.png"):
            r = requests.get(f"{BASE_URL}{path}")
            assert r.status_code == 200, path
            assert r.headers.get("content-type", "").startswith("image/"), f"{path} content-type {r.headers.get('content-type')}"

    def test_index_has_manifest_link(self):
        r = requests.get(f"{BASE_URL}/")
        assert r.status_code == 200
        html = r.text
        assert 'rel="manifest"' in html or "rel='manifest'" in html
        assert "/manifest.json" in html
        assert "apple-touch-icon" in html
