from django.db import models


class Customer(models.Model):
    GENDER_CHOICES = [
        ("M", "Male"),
        ("F", "Female"),
        ("O", "Other"),
    ]

    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20)
    dob = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Claim(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    date_of_loss = models.DateField()
    description_of_loss = models.TextField()
    passport = models.ImageField(upload_to="passport_photos/", blank=True, null=True)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer.name} - {self.date_of_loss}"
