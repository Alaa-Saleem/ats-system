from django import forms
from django.contrib.auth import get_user_model
from apps.accounts.models import Company
from apps.candidates.models import Candidate

User = get_user_model()

SIZE_CHOICES = [
    ('', 'Select size…'),
    ('1-10',    '1–10 employees'),
    ('11-50',   '11–50 employees'),
    ('51-200',  '51–200 employees'),
    ('201-500', '201–500 employees'),
    ('500+',    '500+ employees'),
]


class PersonalInfoForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, required=False, label='First Name')
    last_name  = forms.CharField(max_length=150, required=False, label='Last Name')

    class Meta:
        model  = User
        fields = ['first_name', 'last_name', 'phone', 'location', 'bio', 'avatar']
        widgets = {
            'bio':      forms.Textarea(attrs={'rows': 3}),
            'avatar':   forms.FileInput(),
        }


class CandidateProfessionalForm(forms.ModelForm):
    """For the candidate's global profile (company=None record)."""
    class Meta:
        model  = Candidate
        fields = [
            'current_title', 'years_of_experience', 'skills',
            'bio', 'linkedin_url', 'github_url', 'portfolio_url',
            'availability', 'expected_salary',
        ]
        labels = {
            'current_title':       'Current Job Title',
            'years_of_experience': 'Years of Experience',
            'skills':              'Skills (comma-separated)',
            'availability':        'Availability',
            'expected_salary':     'Expected Salary',
        }
        widgets = {
            'bio':    forms.Textarea(attrs={'rows': 3}),
            'skills': forms.TextInput(attrs={'placeholder': 'Python, Django, React…'}),
        }


class CandidateDocumentsForm(forms.ModelForm):
    class Meta:
        model  = Candidate
        fields = ['cv_file']


class CompanyInfoForm(forms.ModelForm):
    class Meta:
        model  = Company
        fields = [
            'company_name', 'industry', 'company_size',
            'location', 'phone', 'website', 'description', 'logo',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'logo':        forms.FileInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['company_size'].widget = forms.Select(choices=SIZE_CHOICES)


class StaffRoleForm(forms.ModelForm):
    class Meta:
        model  = User
        fields = ['position']
        labels = {'position': 'Your Position / Department'}
