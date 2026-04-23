from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User


class CompanyRegisterForm(UserCreationForm):
    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if not email:
            raise forms.ValidationError("Email is required.")
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("This email is already used.")
        return email

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class CandidateRegisterForm(UserCreationForm):
    full_name = forms.CharField(max_length=255, required=True, label="الاسم الكامل")
    phone = forms.CharField(max_length=30, required=True, label="رقم الهاتف")
    current_title = forms.CharField(max_length=255, required=False, label="المسمى الوظيفي الحالي")
    years_of_experience = forms.IntegerField(required=False, label="سنوات الخبرة")
    location = forms.CharField(max_length=255, required=False, label="الموقع")
    cv_file = forms.FileField(required=True, label="السيرة الذاتية (CV)")

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if not email:
            raise forms.ValidationError("Email is required.")
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("This email is already used.")
        return email

    class Meta:
        model = User
        fields = ['username', 'email']


class TeamMemberCreateForm(UserCreationForm):
    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password1",
            "password2",
            "team_role",
        ]


class TeamMemberPermissionForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["team_role"]
