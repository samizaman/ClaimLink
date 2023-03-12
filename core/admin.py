from django.contrib import admin
from .models import Claim, Customer


class ClaimAdmin(admin.ModelAdmin):
    list_display = ("customer", "id", "date_of_loss", "date_added")
    list_filter = ("date_of_loss", "date_added")
    ordering = ("-date_added",)


class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone_number", "dob", "gender", "date_added")
    search_fields = ("name", "email", "phone_number", "gender")
    ordering = ("-date_added",)


admin.site.register(Claim, ClaimAdmin)
admin.site.register(Customer, CustomerAdmin)
