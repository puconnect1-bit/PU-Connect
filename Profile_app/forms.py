from django import forms
from Profile_app.models import Profile

FACULTY_CHOICES = [
    ('', '— Select faculty —'),
    ('FESAC', 'FESAC — Faculty of Engineering Science & Computing'),
    ('FBA',   'FBA — Faculty of Business Administration'),
    ('FHAS',  'FHAS — Faculty of Health and Allied Sciences'),
    ('FEDU',  'FEDU — Faculty of Education'),
    ('LLB',   'LLB — Faculty of Law'),
]

class PhoneForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['phone', 'faculty']
        widgets = {
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your phone number',
                'required': 'required',
            }),
            'faculty': forms.Select(choices=FACULTY_CHOICES, attrs={'class': 'form-control'}),
        }
