@echo off
cd /d "%~dp0"
python manage.py send_billing_reminders
