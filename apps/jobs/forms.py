from django import forms
from .models import Job
from apps.candidates.models import Candidate


class JobForm(forms.ModelForm):
    application_deadline = forms.DateField(
        widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-input'}),
        input_formats=['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%m/%d/%Y'],
        required=False,
        label='الموعد النهائي'
    )

    class Meta:
        model = Job
        fields = [
            'title', 'description', 'required_skills',
            'location', 'department', 'job_type',
            'salary', 'application_deadline', 'status'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'مثال: مطور واجهات أمامية'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 4, 'placeholder': 'وصف الوظيفة...'}),
            'required_skills': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'المهارات المطلوبة...'}),
            'location': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'مثال: الرياض'}),
            'department': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'مثال: هندسة البرمجيات'}),
            'job_type': forms.Select(attrs={'class': 'form-input'}),
            'salary': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'اختياري'}),
            'status': forms.Select(attrs={'class': 'form-input'}),
        }
        labels = {
            'title': 'المسمى الوظيفي',
            'description': 'الوصف',
            'required_skills': 'المهارات المطلوبة',
            'location': 'الموقع',
            'department': 'القسم',
            'job_type': 'نوع الوظيفة',
            'salary': 'الراتب (اختياري)',
            'status': 'الحالة',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make non-critical fields optional
        self.fields['required_skills'].required = False
        self.fields['location'].required = False
        self.fields['department'].required = False
        self.fields['salary'].required = False
        self.fields['application_deadline'].required = False


class PublicJobApplicationForm(forms.ModelForm):
    class Meta:
        model = Candidate
        fields = [
            "full_name",
            "phone",
            "email",
            "current_title",
            "years_of_experience",
            "location",
            "cv_file",
            "notes",
        ]
