# Deploying to Vercel

Use `member_billing_gentelella` as the Vercel project root directory. This is the folder that contains `manage.py`.

## Required environment variables

Set these in Vercel Project Settings > Environment Variables:

```text
SECRET_KEY=replace-with-a-long-random-secret
DEBUG=false
ALLOWED_HOSTS=.vercel.app,your-domain.com
CSRF_TRUSTED_ORIGINS=https://your-project.vercel.app,https://your-domain.com
DATABASE_URL=postgres://...
```

Optional notification variables:

```text
DEFAULT_FROM_EMAIL=
EMAIL_BACKEND=
EMAIL_HOST=
EMAIL_PORT=
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
EMAIL_USE_TLS=true
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_WHATSAPP_FROM=
TWILIO_SMS_FROM=
```

## Database note

Do not use SQLite for production on Vercel. Vercel serverless deployments have an ephemeral filesystem, so uploaded or written database changes are not safely persisted. Use a hosted Postgres database and set `DATABASE_URL`.

## Deployment steps

```bash
cd member_billing_gentelella
python manage.py check
vercel
```

After the first deployment, run migrations against the production database from a trusted terminal with the same environment variables:

```bash
python manage.py migrate
python manage.py setup_enterprise_roles
python manage.py createsuperuser
```
