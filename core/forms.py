import re
from datetime import date, timedelta

from django import forms


class PersonalDetailsForm(forms.Form):
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(
            attrs={
                "class": "w-full p-2 border rounded",
                "required": True,
                "autofocus": True,
            }
        ),
    )
    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={"class": "w-full p-2 border rounded", "required": True}
        )
    )
    phone_number = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={"class": "flex-grow p-2 border rounded"}),
    )
    dob = forms.DateField(
        input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": "w-full p-2 border rounded",
                "required": True,
            }
        ),
    )
    gender = forms.ChoiceField(
        choices=[("male", "Male"), ("female", "Female"), ("other", "Other")],
        widget=forms.Select(
            attrs={"class": "w-full p-2 border rounded", "required": True}
        ),
    )

    def clean_name(self):
        name = self.cleaned_data.get("name")
        if not re.match("^[a-zA-Z\s]+$", name):
            raise forms.ValidationError("Name should only contain letters and spaces")
        return name

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get("phone_number")
        if not re.match("^\d+$", phone_number):
            raise forms.ValidationError("Phone number should only contain numbers")
        return phone_number

    def clean_dob(self):
        dob = self.cleaned_data.get("dob")
        today = date.today()
        min_age = 18
        min_birthdate = today - timedelta(
            days=min_age * 365 + min_age // 4
        )  # Accounts for leap years

        if dob > min_birthdate:
            raise forms.ValidationError(f"Age must be at least {min_age} years old")
        return dob
