# Membership Billing System with Gentelella-style Dashboard

This is a complete Django system for managing members, automatic billing, payments, and debtors.

## Billing Rules Included

- Every member pays a joining membership fee of **UGX 10,000**.
- After joining, the system calculates subscription fees from the member's joined date.
- A member can be billed:
  - **UGX 5,000 every month**, or
  - **UGX 20,000 every 4 months**.
- The system shows:
  - who owes money,
  - how much each member is expected to pay,
  - how much they have paid,
  - and the exact outstanding balance.

## How to Run

Open this folder in VS Code or terminal.

### 1. Create virtual environment

Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

Mac/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install requirements

```bash
pip install -r requirements.txt
```

### 3. Create database tables

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Create login user

```bash
python manage.py createsuperuser
```

Example:
- username: admin
- password: your password

### 5. Run server

```bash
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

## Main Pages

- Dashboard: `/`
- Members: `/members/`
- Register Member: `/members/add/`
- Record Payment: `/payments/add/`
- Debtors: `/debtors/`
- Reports: `/reports/`
- Django Admin: `/admin/`

## Email and WhatsApp Reminders

The system can send billing reminders by email and WhatsApp with:

```bash
python manage.py send_billing_reminders
```

Test first without sending:

```bash
python manage.py send_billing_reminders --dry-run
```

What it sends:

- on the configured monthly reminder day, active members with an outstanding balance receive a billing reminder;
- members on the 4-month plan also receive a reminder when their due month count reaches a multiple of 4.

Email uses Django settings. By default, emails print in the terminal. To send real email, set environment variables such as:

```text
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your@email.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your@email.com
```

WhatsApp uses Twilio WhatsApp. Set:

```text
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
TWILIO_SMS_FROM=+1234567890
```

Run `run_reminders_windows.bat` daily with Windows Task Scheduler. It records each sent reminder so the same member is not messaged twice for the same reminder date.

The web dashboard also includes:

- Reminder Settings for channels and editable message templates.
- Notification History for sent and failed messages.
- Manual Send Reminder buttons on member detail pages.
- Printable member statements.
- Printable payment receipts after recording payments.
- Dashboard alert counters for reminders due today, failed messages, and members due this week.
- Due Calendar for members whose next payment falls in a selected month.
- Bulk Reminders for sending reminders to many debtors at once.
- CSV exports for members and payments.
- Payment editing and deletion with receipt links.
- Debt aging buckets showing current, 1-29, 30-59, 60-89, and 90+ day balances.
- Audit Trail for member, payment, reminder, settings, export, and delete actions.
- Enterprise roles: Admin, Manager, Accountant, Cashier, Auditor, Read Only.
- Payment approval workflow for edits, deletes, and refunds.
- Member portal for linked member user accounts.
- Payment method, reference, provider, transaction ID, status, and refund tracking.
- Payment confirmation messages and birthday engagement messages.
- Advanced reports with date filters and collections by payment method.
- Password strength rules and session timeout settings.
- Staff follow-up notes on member profiles.
- Member CSV/XLSX Excel import with telephone-number matching and JSON API endpoints for members and payments.

## Note about Gentelella

This project uses a Gentelella-style admin dashboard layout: dark sidebar, top navigation, dashboard tiles, panels, tables, and admin-style pages. Bootstrap and Font Awesome are loaded through CDN for styling.
