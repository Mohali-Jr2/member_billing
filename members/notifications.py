import base64
import json
from urllib import parse, request

from django.conf import settings
from django.core.mail import send_mail
from django.db import IntegrityError

from .models import MessageTemplate, NotificationLog, ReminderSetting


class NotificationConfigurationError(Exception):
    pass


def send_email(member, subject, message):
    if not member.email:
        return False, "Member has no email address."

    sent = send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [member.email],
        fail_silently=False,
    )
    return sent > 0, ""


def send_whatsapp(member, message):
    if not member.phone:
        return False, "Member has no phone number."

    account_sid = settings.TWILIO_ACCOUNT_SID
    auth_token = settings.TWILIO_AUTH_TOKEN
    from_number = settings.TWILIO_WHATSAPP_FROM

    if not account_sid or not auth_token or not from_number:
        raise NotificationConfigurationError("Twilio WhatsApp settings are missing.")

    to_number = _format_whatsapp_number(member.phone)
    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
    data = parse.urlencode(
        {
            "From": _ensure_whatsapp_prefix(from_number),
            "To": to_number,
            "Body": message,
        }
    ).encode("utf-8")

    api_request = request.Request(url, data=data, method="POST")
    credentials = base64.b64encode(f"{account_sid}:{auth_token}".encode("utf-8")).decode("ascii")
    api_request.add_header("Authorization", f"Basic {credentials}")

    try:
        with request.urlopen(api_request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        return False, str(exc)

    return True, payload.get("sid", "")


def send_sms(member, message):
    if not member.phone:
        return False, "Member has no phone number."

    account_sid = settings.TWILIO_ACCOUNT_SID
    auth_token = settings.TWILIO_AUTH_TOKEN
    from_number = settings.TWILIO_SMS_FROM

    if not account_sid or not auth_token or not from_number:
        raise NotificationConfigurationError("Twilio SMS settings are missing.")

    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
    data = parse.urlencode(
        {
            "From": from_number,
            "To": _format_phone_number(member.phone),
            "Body": message,
        }
    ).encode("utf-8")

    api_request = request.Request(url, data=data, method="POST")
    credentials = base64.b64encode(f"{account_sid}:{auth_token}".encode("utf-8")).decode("ascii")
    api_request.add_header("Authorization", f"Basic {credentials}")

    try:
        with request.urlopen(api_request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        return False, str(exc)

    return True, payload.get("sid", "")


def send_member_reminder(member, kind, event_date, force=False):
    MessageTemplate.ensure_defaults()
    template = MessageTemplate.objects.get(kind=kind)
    setting = ReminderSetting.current()
    subject = template.render_subject(member)
    message = template.render_body(member)
    results = []

    if setting.enable_email:
        results.append(_send_logged_channel(member, kind, event_date, NotificationLog.CHANNEL_EMAIL, subject, message, force))

    whatsapp_result = None
    if setting.enable_whatsapp:
        whatsapp_result = _send_logged_channel(
            member,
            kind,
            event_date,
            NotificationLog.CHANNEL_WHATSAPP,
            subject,
            message,
            force,
        )
        results.append(whatsapp_result)

    if setting.enable_sms_fallback and whatsapp_result and whatsapp_result["status"] == NotificationLog.STATUS_FAILED:
        results.append(_send_logged_channel(member, kind, event_date, NotificationLog.CHANNEL_SMS, subject, message, force))

    return subject, message, results


def send_payment_confirmation(payment):
    MessageTemplate.ensure_defaults()
    template = MessageTemplate.objects.get(kind=NotificationLog.KIND_PAYMENT_CONFIRMATION)
    setting = ReminderSetting.current()
    extra_context = {
        "payment_amount": f"{payment.amount:,}",
        "payment_date": payment.payment_date,
        "payment_method": payment.get_method_display(),
        "payment_reference": payment.reference or "N/A",
        "payment_status": payment.get_status_display(),
    }
    subject = template.render_subject(payment.member, extra_context)
    message = template.render_body(payment.member, extra_context)
    results = []

    if setting.enable_email:
        results.append(
            _send_logged_channel(
                payment.member,
                NotificationLog.KIND_PAYMENT_CONFIRMATION,
                payment.payment_date,
                NotificationLog.CHANNEL_EMAIL,
                subject,
                message,
                force=True,
            )
        )

    whatsapp_result = None
    if setting.enable_whatsapp:
        whatsapp_result = _send_logged_channel(
            payment.member,
            NotificationLog.KIND_PAYMENT_CONFIRMATION,
            payment.payment_date,
            NotificationLog.CHANNEL_WHATSAPP,
            subject,
            message,
            force=True,
        )
        results.append(whatsapp_result)

    if setting.enable_sms_fallback and whatsapp_result and whatsapp_result["status"] == NotificationLog.STATUS_FAILED:
        results.append(
            _send_logged_channel(
                payment.member,
                NotificationLog.KIND_PAYMENT_CONFIRMATION,
                payment.payment_date,
                NotificationLog.CHANNEL_SMS,
                subject,
                message,
                force=True,
            )
        )

    return subject, message, results


def _send_logged_channel(member, kind, event_date, channel, subject, message, force):
    if not force and NotificationLog.objects.filter(
        member=member,
        channel=channel,
        kind=kind,
        event_date=event_date,
        status=NotificationLog.STATUS_SENT,
    ).exists():
        return {"channel": channel, "status": "SKIPPED", "error": "Already sent."}

    try:
        if channel == NotificationLog.CHANNEL_EMAIL:
            sent, detail = send_email(member, subject, message)
        elif channel == NotificationLog.CHANNEL_WHATSAPP:
            sent, detail = send_whatsapp(member, message)
        else:
            sent, detail = send_sms(member, message)
        status = NotificationLog.STATUS_SENT if sent else NotificationLog.STATUS_FAILED
        error = "" if sent else detail
    except NotificationConfigurationError as exc:
        status = NotificationLog.STATUS_FAILED
        error = str(exc)
    except Exception as exc:
        status = NotificationLog.STATUS_FAILED
        error = str(exc)

    try:
        NotificationLog.objects.update_or_create(
            member=member,
            channel=channel,
            kind=kind,
            event_date=event_date,
            defaults={
                "status": status,
                "message": message,
                "error": error,
            },
        )
    except IntegrityError:
        return {"channel": channel, "status": "SKIPPED", "error": "Already recorded."}

    return {"channel": channel, "status": status, "error": error}


def _format_whatsapp_number(phone):
    return _ensure_whatsapp_prefix(_format_phone_number(phone))


def _format_phone_number(phone):
    cleaned = "".join(char for char in phone.strip() if char.isdigit() or char == "+")

    if cleaned.startswith("0"):
        cleaned = "+256" + cleaned[1:]
    elif cleaned.startswith("256"):
        cleaned = "+" + cleaned
    elif not cleaned.startswith("+"):
        cleaned = "+" + cleaned

    return cleaned


def _ensure_whatsapp_prefix(number):
    if number.startswith("whatsapp:"):
        return number
    return f"whatsapp:{number}"
