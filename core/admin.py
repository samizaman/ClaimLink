from django.contrib import admin
from .models import Claim, Customer


class ClaimAdmin(admin.ModelAdmin):
    list_display = ("customer", "id", "date_of_loss", "timestamp")
    list_filter = ("date_of_loss", "timestamp")
    ordering = ("-timestamp",)


class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone_number", "dob", "gender", "timestamp")
    search_fields = ("name", "email", "phone_number", "gender")
    ordering = ("-timestamp",)


admin.site.register(Claim, ClaimAdmin)
admin.site.register(Customer, CustomerAdmin)
