import re
from datetime import date, timedelta

from django import forms

from core.models import COUNTRY_CHOICES, CURRENCY_CHOICES

COUNTRY_CHOICES = [("", "Select a country")] + COUNTRY_CHOICES
CURRENCY_CHOICES = [("", "Select a currency")] + CURRENCY_CHOICES


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
        choices=[
            ("", "Select a gender"),
            ("male", "Male"),
            ("female", "Female"),
            ("other", "Other"),
        ],
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

    # def clean_dob(self):
    #     dob = self.cleaned_data.get("dob")
    #     today = date.today()
    #     min_age = 18
    #     min_birthdate = today - timedelta(
    #         days=min_age * 365 + min_age // 4
    #     )  # Accounts for leap years
    #
    #     if dob > min_birthdate:
    #         raise forms.ValidationError(f"Age must be at least {min_age} years old")
    #     return dob


class ClaimDetailsForm(forms.Form):
    date_of_loss = forms.DateField(
        widget=forms.DateInput(
            attrs={"type": "date", "class": "w-full p-2 border rounded"}
        ),
        input_formats=["%Y-%m-%d"],
    )
    country_of_incident = forms.ChoiceField(
        choices=COUNTRY_CHOICES,
        widget=forms.Select(attrs={"class": "w-full p-2 border rounded"}),
    )
    claim_amount_currency = forms.ChoiceField(
        choices=CURRENCY_CHOICES,
        widget=forms.Select(attrs={"class": "w-full p-2 border rounded"}),
    )
    claim_amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(
            attrs={
                "class": "w-full p-2 border rounded",
                "placeholder": "Enter claim amount",
            }
        ),
    )
    description_of_loss = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "class": "w-full p-2 border rounded",
                "rows": 4,
                "placeholder": "Provide a brief description of the loss",
            }
        )
    )
