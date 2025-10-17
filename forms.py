from django import forms
from django.contrib.auth.models import User
from .models import UserProfile

class UserForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=True, label="First Name")
    last_name = forms.CharField(max_length=30, required=True, label="Last Name")
    email = forms.CharField(max_length=60, required=True, label='email')

    class Meta:
        model = User
        fields = ["first_name", "last_name"]


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ["phone", "school_name"]
        widgets = {
            "phone": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Phone Number"}),
            "school_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "School Name"}),
        }
        labels = {
            "phone": "Phone Number",
            "school_name": "School Name",
        }

