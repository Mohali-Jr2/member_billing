from django.db import models
from django.utils import timezone
import calendar


JOINING_FEE = 10000
MONTHLY_FEE = 5000
FOUR_MONTH_FEE = 20000


class Member(models.Model):
    PLAN_MONTHLY = "MONTHLY"
    PLAN_FOUR_MONTHS = "FOUR_MONTHS"

    PLAN_CHOICES = [
        (PLAN_MONTHLY, "Monthly - UGX 5,000"),
        (PLAN_FOUR_MONTHS, "Every 4 Months - UGX 20,000"),
    ]

    member_id = models.CharField(max_length=20, unique=True, blank=True)
    full_name = models.CharField(max_length=120)
    user = models.OneToOneField("auth.User", on_delete=models.SET_NULL, blank=True, null=True, related_name="member_profile")
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    date_of_birth = models.DateField(blank=True, null=True)
    joined_date = models.DateField(default=timezone.now)
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default=PLAN_MONTHLY)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["full_name"]

    def months_due(self):
        return self.months_due_on(timezone.localdate())

    def months_due_on(self, date):
        if self.joined_date > date:
            return 0

        months = (date.year - self.joined_date.year) * 12 + (date.month - self.joined_date.month)

        # Count the current billing month only after the member reaches their join day.
        if date.day >= self.joined_date.day:
            months += 1

        return max(months, 0)

    def billing_periods_due(self):
        months = self.months_due()
        if self.plan == self.PLAN_MONTHLY:
            return months
        return (months + 3) // 4

    def next_due_date(self):
        today = timezone.localdate()
        if self.joined_date > today:
            return self.joined_date

        interval = 1 if self.plan == self.PLAN_MONTHLY else 4
        periods = max((self.months_due_on(today) + interval - 1) // interval, 0)
        due_date = add_months(self.joined_date, periods * interval)
        if due_date <= today:
            due_date = add_months(due_date, interval)
        return due_date

    def days_overdue(self):
        if self.balance() <= 0:
            return 0
        return max((timezone.localdate() - self.next_due_date()).days, 0)

    def overdue_bucket(self):
        days = self.days_overdue()
        if days >= 90:
            return "90+ days"
        if days >= 60:
            return "60-89 days"
        if days >= 30:
            return "30-59 days"
        if days > 0:
            return "1-29 days"
        return "Current"

    def membership_charge(self):
        return JOINING_FEE

    def subscription_charge(self):
        if self.plan == self.PLAN_MONTHLY:
            return self.months_due() * MONTHLY_FEE
        return self.billing_periods_due() * FOUR_MONTH_FEE

    def total_expected(self):
        return self.membership_charge() + self.subscription_charge()

    def total_paid(self):
        result = self.payments.aggregate(total=models.Sum("amount"))
        return result["total"] or 0

    def balance(self):
        return self.total_expected() - self.total_paid()

    def status(self):
        if self.balance() > 0:
            return "Debtor"
        if self.balance() < 0:
            return "Overpaid"
        return "Cleared"

    def is_debtor(self):
        return self.balance() > 0

    def demand_breakdown(self):
        if self.plan == self.PLAN_MONTHLY:
            plan_text = f"{self.months_due()} month(s) × UGX {MONTHLY_FEE:,}"
        else:
            plan_text = f"{self.billing_periods_due()} period(s) × UGX {FOUR_MONTH_FEE:,}"
        return {
            "joining_fee": JOINING_FEE,
            "subscription_text": plan_text,
            "subscription_charge": self.subscription_charge(),
            "expected": self.total_expected(),
            "paid": self.total_paid(),
            "balance": self.balance(),
        }

    def __str__(self):
        return self.full_name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.member_id:
            self.member_id = f"COD-{self.pk:04d}"
            super().save(update_fields=["member_id"])


class Payment(models.Model):
    METHOD_CASH = "CASH"
    METHOD_MOBILE_MONEY = "MOBILE_MONEY"
    METHOD_BANK = "BANK"
    METHOD_CARD = "CARD"
    METHOD_ONLINE = "ONLINE"
    METHOD_CHOICES = [
        (METHOD_CASH, "Cash"),
        (METHOD_MOBILE_MONEY, "Mobile money"),
        (METHOD_BANK, "Bank transfer"),
        (METHOD_CARD, "Card"),
        (METHOD_ONLINE, "Online"),
    ]

    STATUS_COMPLETED = "COMPLETED"
    STATUS_PENDING = "PENDING"
    STATUS_REFUNDED = "REFUNDED"
    STATUS_CHOICES = [
        (STATUS_COMPLETED, "Completed"),
        (STATUS_PENDING, "Pending"),
        (STATUS_REFUNDED, "Refunded"),
    ]

    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="payments")
    amount = models.PositiveIntegerField()
    payment_date = models.DateField(default=timezone.now)
    method = models.CharField(max_length=30, choices=METHOD_CHOICES, default=METHOD_CASH)
    reference = models.CharField(max_length=80, blank=True)
    provider = models.CharField(max_length=80, blank=True)
    external_transaction_id = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_COMPLETED)
    refunded_amount = models.PositiveIntegerField(default=0)
    refund_reason = models.TextField(blank=True)
    received_by = models.CharField(max_length=100, blank=True)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-payment_date", "-created_at"]

    def __str__(self):
        return f"{self.member.full_name} - UGX {self.amount:,}"


class NotificationLog(models.Model):
    CHANNEL_EMAIL = "EMAIL"
    CHANNEL_WHATSAPP = "WHATSAPP"
    CHANNEL_SMS = "SMS"
    CHANNEL_CHOICES = [
        (CHANNEL_EMAIL, "Email"),
        (CHANNEL_WHATSAPP, "WhatsApp"),
        (CHANNEL_SMS, "SMS"),
    ]

    KIND_MONTHLY_START = "MONTHLY_START"
    KIND_FOUR_MONTH_REMINDER = "FOUR_MONTH_REMINDER"
    KIND_PAYMENT_CONFIRMATION = "PAYMENT_CONFIRMATION"
    KIND_BIRTHDAY = "BIRTHDAY"
    KIND_CHOICES = [
        (KIND_MONTHLY_START, "New month reminder"),
        (KIND_FOUR_MONTH_REMINDER, "Four month payment reminder"),
        (KIND_PAYMENT_CONFIRMATION, "Payment confirmation"),
        (KIND_BIRTHDAY, "Birthday message"),
    ]

    STATUS_SENT = "SENT"
    STATUS_FAILED = "FAILED"
    STATUS_CHOICES = [
        (STATUS_SENT, "Sent"),
        (STATUS_FAILED, "Failed"),
    ]

    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="notification_logs")
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES)
    kind = models.CharField(max_length=40, choices=KIND_CHOICES)
    event_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    message = models.TextField()
    error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["member", "channel", "kind", "event_date"],
                name="unique_member_notification_per_event",
            )
        ]

    def __str__(self):
        return f"{self.member.full_name} - {self.kind} - {self.channel}"


class ReminderSetting(models.Model):
    monthly_reminder_day = models.PositiveSmallIntegerField(default=1)
    enable_email = models.BooleanField(default=True)
    enable_whatsapp = models.BooleanField(default=True)
    enable_sms_fallback = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Reminder setting"
        verbose_name_plural = "Reminder settings"

    def save(self, *args, **kwargs):
        self.monthly_reminder_day = min(max(self.monthly_reminder_day, 1), 28)
        super().save(*args, **kwargs)

    @classmethod
    def current(cls):
        setting, _ = cls.objects.get_or_create(pk=1)
        return setting

    def __str__(self):
        return "Reminder settings"


class MessageTemplate(models.Model):
    kind = models.CharField(max_length=40, choices=NotificationLog.KIND_CHOICES, unique=True)
    subject = models.CharField(max_length=160)
    body = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["kind"]

    @classmethod
    def defaults(cls):
        return {
            NotificationLog.KIND_MONTHLY_START: {
                "subject": "New month billing reminder",
                "body": (
                    "Hello {full_name}, a new billing month has started. "
                    "Your current outstanding balance is UGX {balance}. "
                    "Please make your payment as soon as possible. Thank you."
                ),
            },
            NotificationLog.KIND_FOUR_MONTH_REMINDER: {
                "subject": "Four month payment reminder",
                "body": (
                    "Hello {full_name}, this is a reminder for your 4-month payment plan. "
                    "Your current outstanding balance is UGX {balance}. "
                    "Please pay to keep your membership up to date. Thank you."
                ),
            },
            NotificationLog.KIND_PAYMENT_CONFIRMATION: {
                "subject": "Payment received",
                "body": (
                    "Hello {full_name}, your payment of UGX {payment_amount} "
                    "paid on {payment_date} has been attached to your account. "
                    "Your current outstanding balance is UGX {balance}. Thank you."
                ),
            },
            NotificationLog.KIND_BIRTHDAY: {
                "subject": "Happy birthday",
                "body": "Happy birthday {full_name}. We appreciate your membership and wish you a wonderful day.",
            },
        }

    @classmethod
    def ensure_defaults(cls):
        for kind, values in cls.defaults().items():
            cls.objects.get_or_create(kind=kind, defaults=values)

    def render_subject(self, member, extra_context=None):
        context = template_context(member)
        if extra_context:
            context.update(extra_context)
        return self.subject.format(**context)

    def render_body(self, member, extra_context=None):
        context = template_context(member)
        if extra_context:
            context.update(extra_context)
        return self.body.format(**context)

    def __str__(self):
        return self.get_kind_display()


class AuditLog(models.Model):
    ACTION_CREATE = "CREATE"
    ACTION_UPDATE = "UPDATE"
    ACTION_DELETE = "DELETE"
    ACTION_SEND_REMINDER = "SEND_REMINDER"
    ACTION_BULK_REMINDER = "BULK_REMINDER"
    ACTION_EXPORT = "EXPORT"
    ACTION_SETTINGS = "SETTINGS"
    ACTION_CHOICES = [
        (ACTION_CREATE, "Create"),
        (ACTION_UPDATE, "Update"),
        (ACTION_DELETE, "Delete"),
        (ACTION_SEND_REMINDER, "Send reminder"),
        (ACTION_BULK_REMINDER, "Bulk reminder"),
        (ACTION_EXPORT, "Export"),
        (ACTION_SETTINGS, "Settings"),
    ]

    user = models.ForeignKey("auth.User", on_delete=models.SET_NULL, blank=True, null=True)
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    object_type = models.CharField(max_length=80)
    object_id = models.CharField(max_length=80, blank=True)
    object_repr = models.CharField(max_length=255, blank=True)
    details = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_action_display()} {self.object_type} by {self.user or 'System'}"


class PaymentApprovalRequest(models.Model):
    ACTION_EDIT = "EDIT"
    ACTION_DELETE = "DELETE"
    ACTION_REFUND = "REFUND"
    ACTION_CHOICES = [
        (ACTION_EDIT, "Edit payment"),
        (ACTION_DELETE, "Delete payment"),
        (ACTION_REFUND, "Refund payment"),
    ]

    STATUS_PENDING = "PENDING"
    STATUS_APPROVED = "APPROVED"
    STATUS_REJECTED = "REJECTED"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
    ]

    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name="approval_requests")
    requested_by = models.ForeignKey("auth.User", on_delete=models.SET_NULL, blank=True, null=True, related_name="payment_requests")
    reviewed_by = models.ForeignKey("auth.User", on_delete=models.SET_NULL, blank=True, null=True, related_name="reviewed_payment_requests")
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    reason = models.TextField(blank=True)
    proposed_data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_action_display()} request for {self.payment}"


class ActivityFundRequest(models.Model):
    STATUS_PENDING = "PENDING"
    STATUS_APPROVED = "APPROVED"
    STATUS_REJECTED = "REJECTED"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
    ]

    activity_title = models.CharField(max_length=160)
    description = models.TextField()
    amount = models.PositiveIntegerField()
    requested_by = models.ForeignKey("auth.User", on_delete=models.SET_NULL, blank=True, null=True, related_name="activity_fund_requests")
    reviewed_by = models.ForeignKey("auth.User", on_delete=models.SET_NULL, blank=True, null=True, related_name="reviewed_activity_fund_requests")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    review_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.activity_title} - UGX {self.amount:,}"


class ReconciliationImport(models.Model):
    STATUS_UNMATCHED = "UNMATCHED"
    STATUS_MATCHED = "MATCHED"
    STATUS_POSTED = "POSTED"
    STATUS_CHOICES = [
        (STATUS_UNMATCHED, "Unmatched"),
        (STATUS_MATCHED, "Matched"),
        (STATUS_POSTED, "Posted"),
    ]

    provider = models.CharField(max_length=80)
    transaction_id = models.CharField(max_length=120)
    payer_phone = models.CharField(max_length=40, blank=True)
    payer_name = models.CharField(max_length=120, blank=True)
    amount = models.PositiveIntegerField()
    paid_at = models.DateTimeField(default=timezone.now)
    matched_member = models.ForeignKey(Member, on_delete=models.SET_NULL, blank=True, null=True, related_name="reconciliation_rows")
    posted_payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, blank=True, null=True, related_name="reconciliation_rows")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_UNMATCHED)
    raw_data = models.JSONField(default=dict, blank=True)
    imported_by = models.ForeignKey("auth.User", on_delete=models.SET_NULL, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-paid_at"]
        constraints = [
            models.UniqueConstraint(fields=["provider", "transaction_id"], name="unique_reconciliation_transaction")
        ]

    def __str__(self):
        return f"{self.provider} {self.transaction_id} - UGX {self.amount:,}"


class MemberNote(models.Model):
    STATUS_OPEN = "OPEN"
    STATUS_DONE = "DONE"
    STATUS_CHOICES = [
        (STATUS_OPEN, "Open"),
        (STATUS_DONE, "Done"),
    ]

    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="staff_notes")
    created_by = models.ForeignKey("auth.User", on_delete=models.SET_NULL, blank=True, null=True)
    note = models.TextField()
    follow_up_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.member.full_name} note"


class UserSecurityProfile(models.Model):
    user = models.OneToOneField("auth.User", on_delete=models.CASCADE, related_name="security_profile")
    two_factor_enabled = models.BooleanField(default=False)
    two_factor_secret = models.CharField(max_length=120, blank=True)
    last_password_change = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Security profile for {self.user.username}"


def template_context(member):
    return {
        "member_id": member.member_id,
        "full_name": member.full_name,
        "phone": member.phone,
        "email": member.email,
        "balance": f"{member.balance():,}",
        "next_due_date": member.next_due_date(),
        "plan": member.get_plan_display(),
    }


def add_months(date, months):
    month_index = date.month - 1 + months
    year = date.year + month_index // 12
    month = month_index % 12 + 1
    day = min(date.day, calendar.monthrange(year, month)[1])
    return date.replace(year=year, month=month, day=day)
