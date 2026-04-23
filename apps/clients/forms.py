from django import forms
from .models import Client, ClientContact

class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['name', 'industry', 'website', 'phone', 'email', 'address', 'notes']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 4}),
        }

class ClientContactForm(forms.ModelForm):
    class Meta:
        model = ClientContact
        fields = ['name', 'title', 'phone', 'email', 'is_primary']
