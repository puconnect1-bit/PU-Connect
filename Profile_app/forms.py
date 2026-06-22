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


class ProfileSetupForm(forms.Form):
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'Your full name', 'autocomplete': 'name'}),
    )
    username = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'placeholder': 'Choose a username', 'autocomplete': 'username'}),
    )
    phone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'placeholder': '024 000 0000', 'type': 'tel'}),
    )
    faculty = forms.ChoiceField(choices=FACULTY_CHOICES)

    def clean_username(self):
        from django.contrib.auth.models import User
        import re
        username = self.cleaned_data['username'].strip().lstrip('@')
        if not re.match(r'^[\w.]+$', username):
            raise forms.ValidationError('Only letters, numbers, underscores and dots allowed.')
        if User.objects.filter(username__iexact=username).exclude(pk=self.initial.get('user_pk')).exists():
            raise forms.ValidationError('That username is already taken.')
        return username

    def clean_faculty(self):
        faculty = self.cleaned_data['faculty']
        if not faculty:
            raise forms.ValidationError('Please select your faculty.')
        return faculty
