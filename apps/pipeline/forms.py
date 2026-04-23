from django import forms
from .models import Application
from apps.candidates.models import Candidate
from apps.jobs.models import Job
from .models import PipelineStage

class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['candidate', 'job', 'current_stage', 'source']

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        if company:
            self.fields['candidate'].queryset = Candidate.objects.filter(company=company)
            self.fields['job'].queryset = Job.objects.filter(company=company, status='open')
        # set default stage if there's any
        first_stage = PipelineStage.objects.order_by('order').first()
        if first_stage:
            self.fields['current_stage'].initial = first_stage
