from uuid import uuid4

import pycountry
from django.db import models
from django.utils import timezone

COUNTRY_CHOICES = sorted(
    [(x.alpha_2, x.name) for x in pycountry.countries], key=lambda x: x[1]
)
CURRENCY_CHOICES = sorted(
    [(x.alpha_3, x.name) for x in pycountry.currencies], key=lambda x: x[1]
)


class Customer(models.Model):
    GENDER_CHOICES = [
        ("M", "Male"),
        ("F", "Female"),
        ("O", "Other"),
    ]

    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    phone_number = models.CharField(
        max_length=15, unique=False, null=True, default=None
    )
    dob = models.DateField(
        null=True, help_text="Date of birth in the format YYYY-MM-DD"
    )
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default="O")
    created_on = models.DateTimeField(
        default=timezone.now, editable=False, null=False, blank=False
    )
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name


class CoverageItem(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Claim(models.Model):
    STATUS_CHOICES = (
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    )
    customer = models.ForeignKey(Customer, models.PROTECT, null=True, blank=True)
    date_of_loss = models.DateField()
    description_of_loss = models.TextField()
    passport = models.ImageField(upload_to="passport_photos/", blank=True, null=True)
    created_on = models.DateTimeField(
        default=timezone.now, editable=False, null=False, blank=False
    )
    timestamp = models.DateTimeField(default=timezone.now)
    claim_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    claim_reference_number = models.CharField(
        max_length=255, default="", null=True, blank=True, unique=False
    )
    country_of_incident = models.CharField(
        blank=True, max_length=2, choices=COUNTRY_CHOICES
    )
    claim_amount_currency = models.CharField(
        blank=True, max_length=8, choices=CURRENCY_CHOICES, default="AED"
    )
    coverage_items = models.ManyToManyField(CoverageItem)
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="approved",
    )
    reasons = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.claim_reference_number}"

    @staticmethod
    def generate_claim_reference_number():
        unique_id = uuid4().hex[:6].upper()
        return f"CL-{unique_id}"

    def save(self, *args, **kwargs):
        if not self.claim_reference_number:
            self.claim_reference_number = self.generate_claim_reference_number()
        super().save(*args, **kwargs)


class Blockchain(models.Model):
    network_name = models.CharField(max_length=255)
    network_url = models.URLField()

    def __str__(self):
        return self.network_name


class Block(models.Model):
    blockchain = models.ForeignKey(Blockchain, models.PROTECT, null=True, blank=True)
    customer = models.ForeignKey(Customer, models.PROTECT, null=True, blank=True)
    claim = models.ForeignKey(Claim, models.PROTECT, null=True, blank=True)
    block_number = models.IntegerField()
    block_hash = models.CharField(max_length=255)
    previous_block_hash = models.CharField(max_length=255)
    timestamp = models.DateTimeField()

    def __str__(self):
        return f"Block {self.block_number}"
