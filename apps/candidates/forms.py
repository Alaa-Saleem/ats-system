from django import forms
from .models import Candidate

class CandidateForm(forms.ModelForm):
    class Meta:
        model = Candidate
        fields = ['full_name', 'phone', 'email', 'current_title', 'years_of_experience', 
                  'expected_salary', 'availability', 'location', 'cv_file', 'notes']
