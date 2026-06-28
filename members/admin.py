from django.contrib import admin
from .models import (
    ActivityFundRequest,
    AuditLog,
    Member,
    MemberNote,
    MessageTemplate,
    NotificationLog,
    Payment,
    PaymentApprovalRequest,
    ReminderSetting,
    UserSecurityProfile,
)


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ("member_id", "full_name", "phone", "email", "joined_date", "plan", "total_expected", "total_paid", "balance", "status", "is_active")
    list_filter = ("plan", "is_active", "joined_date")
    search_fields = ("member_id", "full_name", "phone", "email")
    readonly_fields = ("member_id",)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("member", "amount", "payment_date", "method", "reference", "status", "received_by")
    list_filter = ("payment_date", "method", "status")
    search_fields = ("member__full_name", "reference", "external_transaction_id", "received_by", "note")


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ("member", "channel", "kind", "event_date", "status", "created_at")
    list_filter = ("channel", "kind", "status", "event_date")
    search_fields = ("member__full_name", "member__phone", "member__email", "message", "error")
    readonly_fields = ("member", "channel", "kind", "event_date", "status", "message", "error", "created_at")


@admin.register(ReminderSetting)
class ReminderSettingAdmin(admin.ModelAdmin):
    list_display = ("monthly_reminder_day", "enable_email", "enable_whatsapp", "enable_sms_fallback", "updated_at")


@admin.register(MessageTemplate)
class MessageTemplateAdmin(admin.ModelAdmin):
    list_display = ("kind", "subject", "updated_at")
    search_fields = ("subject", "body")


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "user", "action", "object_type", "object_repr", "ip_address")
    list_filter = ("action", "object_type", "created_at")
    search_fields = ("user__username", "object_type", "object_repr", "details", "ip_address")
    readonly_fields = ("user", "action", "object_type", "object_id", "object_repr", "details", "ip_address", "created_at")


@admin.register(PaymentApprovalRequest)
class PaymentApprovalRequestAdmin(admin.ModelAdmin):
    list_display = ("payment", "action", "status", "requested_by", "reviewed_by", "created_at")
    list_filter = ("action", "status", "created_at")
    search_fields = ("payment__member__full_name", "reason")


@admin.register(ActivityFundRequest)
class ActivityFundRequestAdmin(admin.ModelAdmin):
    list_display = ("activity_title", "amount", "status", "requested_by", "reviewed_by", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("activity_title", "description", "requested_by__username")


@admin.register(MemberNote)
class MemberNoteAdmin(admin.ModelAdmin):
    list_display = ("member", "status", "follow_up_date", "created_by", "created_at")
    list_filter = ("status", "follow_up_date")
    search_fields = ("member__full_name", "note")


@admin.register(UserSecurityProfile)
class UserSecurityProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "two_factor_enabled", "last_password_change")
