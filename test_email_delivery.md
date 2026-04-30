# Email Delivery Test Guide

## Current Configuration ✅

**Email Delivery Method:** Direct to all recipients (not CC)
**Total Recipients Per Email:** 10 (1 applicant + 9 admins)

## How It Works

When an admin approves or rejects a visa application:

1. **System fetches all admin emails from database**
   - Queries: `db.users.find({role: "admin"})`
   - Returns 9 admin email addresses

2. **Combines applicant + admin emails**
   ```python
   all_recipients = [applicant_email] + admin_emails
   # Example: 10 total recipients
   ```

3. **Sends ONE email to ALL recipients**
   ```python
   params = {
       "from": "onboarding@resend.dev",
       "to": [
           "applicant@example.com",
           "Fardaan.tareen@gmail.com",
           "ftareen@dohacollege.com.qa",
           "salmadani@dohacollege.com.qa",
           "malfaarizqi@dohacollege.com.qa",
           "mmehdi@dohacollege.com.qa",
           "vnovruz@dohacollege.com.qa",
           "adfaheem@dohacollege.com.qa",
           "admin@meowls.gov",
           "admin.test@example.com"
       ],
       "subject": "🎉 Your Meowls Visa is APPROVED!",
       "html": "...",
       "attachments": [visa_pdf]
   }
   ```

## All Admin Emails Receiving Notifications

1. **Fardaan.tareen@gmail.com** - Fardaan Tareen
2. **ftareen@dohacollege.com.qa** - F Tareen
3. **salmadani@dohacollege.com.qa** - S Almadani
4. **malfaarizqi@dohacollege.com.qa** - M Alfaarizqi
5. **mmehdi@dohacollege.com.qa** - M Mehdi
6. **vnovruz@dohacollege.com.qa** - V Novruz
7. **adfaheem@dohacollege.com.qa** - AD Faheem
8. **admin@meowls.gov** - Admin User
9. **admin.test@example.com** - Admin Test User

## Testing the Email System

### Step 1: Create a Test Application
1. Go to: https://meowls-visa.preview.emergentagent.com/register
2. Register with a test email you can access
3. Complete the visa application form
4. Upload documents (passport and photo)
5. Submit the application

### Step 2: Admin Reviews Application
1. Login to admin account
2. Go to Admin panel
3. Find the test application
4. Click "Review"
5. Click "Quick Approve" or "Quick Reject"
6. Click "Update Status"

### Step 3: Verify Emails Received
Check that ALL 10 email addresses received the notification:
- ✅ Test applicant email (your test email)
- ✅ Fardaan.tareen@gmail.com
- ✅ ftareen@dohacollege.com.qa
- ✅ salmadani@dohacollege.com.qa
- ✅ malfaarizqi@dohacollege.com.qa
- ✅ mmehdi@dohacollege.com.qa
- ✅ vnovruz@dohacollege.com.qa
- ✅ adfaheem@dohacollege.com.qa
- ✅ admin@meowls.gov
- ✅ admin.test@example.com

## Troubleshooting

### If emails are not received:

1. **Check spam/junk folder** - Resend emails might go to spam initially
2. **Verify admin accounts exist:**
   ```bash
   mongosh test_database --eval "db.users.find({role: 'admin'}, {email: 1, name: 1})"
   ```
3. **Check backend logs for errors:**
   ```bash
   tail -f /var/log/supervisor/backend.err.log | grep -i email
   ```
4. **Verify Resend API key is valid** in `/app/backend/.env`

## Important Notes

- 📧 **All admins receive every email** - there's no filtering
- 🔄 **Emails sent immediately** - async processing, non-blocking
- 📎 **Approvals include PDF** - with AI-generated content + photo
- ❌ **Rejections are text-only** - no attachments
- ⏱️ **Delivery time** - Usually within seconds via Resend

---

**Last Updated:** January 26, 2026
**Email Service:** Resend API
**Sender:** onboarding@resend.dev
