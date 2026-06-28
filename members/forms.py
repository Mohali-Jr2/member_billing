from django import forms
from django.contrib.auth import get_user_model
from .models import ActivityFundRequest, Member, MemberNote, MessageTemplate, Payment, ReminderSetting


class MemberForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = ["full_name", "phone", "email", "joined_date", "plan", "is_active"]
        widgets = {
            "full_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Full name"}),
            "phone": forms.TextInput(attrs={"class": "form-control", "placeholder": "Phone number"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "Email address"}),
            "joined_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "plan": forms.Select(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "flat"}),
        }


class MemberPortalAccessForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = ["user"]
        labels = {"user": "Portal login account"}
        widgets = {
            "user": forms.Select(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        User = get_user_model()
        current_user_id = self.instance.user_id if self.instance and self.instance.pk else None
        linked_user_ids = Member.objects.exclude(pk=self.instance.pk).exclude(user__isnull=True).values_list("user_id", flat=True)
        self.fields["user"].queryset = User.objects.exclude(pk__in=linked_user_ids).order_by("username")
        self.fields["user"].required = False
        self.fields["user"].empty_label = "No portal account"
        if current_user_id:
            self.fields["user"].initial = current_user_id


class MemberChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, member):
        phone = member.phone or "No phone"
        return f"{member.full_name} - {member.member_id} - {phone}"


class PaymentForm(forms.ModelForm):
    member = MemberChoiceField(queryset=Member.objects.all(), widget=forms.Select(attrs={"class": "form-control member-search-select"}))

    class Meta:
        model = Payment
        fields = [
            "member",
            "amount",
            "payment_date",
            "method",
            "reference",
            "provider",
            "external_transaction_id",
            "status",
            "received_by",
            "note",
        ]
        widgets = {
            "amount": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Amount paid"}),
            "payment_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "method": forms.Select(attrs={"class": "form-control"}),
            "reference": forms.TextInput(attrs={"class": "form-control", "placeholder": "Receipt or transaction reference"}),
            "provider": forms.TextInput(attrs={"class": "form-control", "placeholder": "MTN, Airtel, bank, card provider"}),
            "external_transaction_id": forms.TextInput(attrs={"class": "form-control", "placeholder": "External transaction ID"}),
            "status": forms.Select(attrs={"class": "form-control"}),
            "received_by": forms.TextInput(attrs={"class": "form-control", "placeholder": "Received by"}),
            "note": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class PaymentCreateForm(forms.ModelForm):
    member = MemberChoiceField(queryset=Member.objects.all(), widget=forms.Select(attrs={"class": "form-control member-search-select"}))

    def __init__(self, *args, **kwargs):
        received_by_name = kwargs.pop("received_by_name", "")
        super().__init__(*args, **kwargs)
        self.fields["received_by"].initial = received_by_name
        self.fields["received_by"].disabled = True
        self.fields["received_by"].help_text = "Automatically filled from the logged-in account."

    class Meta:
        model = Payment
        fields = [
            "member",
            "amount",
            "payment_date",
            "method",
            "received_by",
        ]
        widgets = {
            "amount": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Amount paid"}),
            "payment_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "method": forms.Select(attrs={"class": "form-control"}),
            "received_by": forms.TextInput(attrs={"class": "form-control", "placeholder": "Received by"}),
        }


class RefundForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ["refunded_amount", "refund_reason"]
        widgets = {
            "refunded_amount": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Amount refunded"}),
            "refund_reason": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class ActivityFundRequestForm(forms.ModelForm):
    class Meta:
        model = ActivityFundRequest
        fields = ["activity_title", "description", "amount"]
        widgets = {
            "activity_title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Activity name"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4, "placeholder": "Describe what the activity is and why money is needed"}),
            "amount": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Amount requested"}),
        }


class MemberNoteForm(forms.ModelForm):
    class Meta:
        model = MemberNote
        fields = ["note", "follow_up_date", "status"]
        widgets = {
            "note": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Follow-up note"}),
            "follow_up_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-control"}),
        }


class MemberImportForm(forms.Form):
    file = forms.FileField(widget=forms.ClearableFileInput(attrs={"class": "form-control-file"}))


class PublicPortalAccessForm(forms.Form):
    member_id = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Member ID, e.g. COD-0001"}))
    phone = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Phone number"}))


class ReminderSettingForm(forms.ModelForm):
    class Meta:
        model = ReminderSetting
        fields = ["monthly_reminder_day", "enable_email", "enable_whatsapp", "enable_sms_fallback"]
        widgets = {
            "monthly_reminder_day": forms.NumberInput(attrs={"class": "form-control", "min": 1, "max": 28}),
            "enable_email": forms.CheckboxInput(attrs={"class": "flat"}),
            "enable_whatsapp": forms.CheckboxInput(attrs={"class": "flat"}),
            "enable_sms_fallback": forms.CheckboxInput(attrs={"class": "flat"}),
        }


class MessageTemplateForm(forms.ModelForm):
    class Meta:
        model = MessageTemplate
        fields = ["subject", "body"]
        widgets = {
            "subject": forms.TextInput(attrs={"class": "form-control"}),
            "body": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
        }
