import csv

from django.contrib import admin
from django.http import HttpResponse
from django.urls import path

from .models import Block, Blockchain, Claim, CoverageItem, Customer


class ExportCsvMixin:
    def export_as_csv(self, request, queryset):
        meta = self.model._meta
        field_names = [field.name for field in meta.fields]
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f"attachment; filename={meta}.csv"
        writer = csv.writer(response)
        writer.writerow(field_names)
        for obj in queryset.all():
            row = writer.writerow([getattr(obj, field) for field in field_names])
        return response

    export_as_csv.short_description = "Export Selected as CSV"

    def export_all_as_csv(self, request):
        queryset = self.model.objects.all()
        return self.export_as_csv(request, queryset)


class ClaimAdmin(admin.ModelAdmin, ExportCsvMixin):
    list_display = (
        "claim_reference_number",
        "customer",
        "date_of_loss",
        "claim_amount",
        "status",
        "severity",
        "timestamp",
    )
    list_filter = (
        "status",
        "severity",
        "country_of_incident",
    )
    search_fields = ("customer__name", "description_of_loss", "claim_reference_number")
    ordering = ("-timestamp",)
    actions = ["export_as_csv"]

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path("export_all_as_csv/", self.export_all_as_csv),
        ]
        return my_urls + urls


class CustomerAdmin(admin.ModelAdmin, ExportCsvMixin):
    list_display = (
        "name",
        "email",
        "phone_number",
        "dob",
        "gender",
        "created_on",
        "timestamp",
    )
    search_fields = ("name", "email", "phone_number", "gender")
    ordering = ("-timestamp",)


class BlockchainAdmin(admin.ModelAdmin):
    list_display = ("network_name", "network_url")


class BlockAdmin(admin.ModelAdmin, ExportCsvMixin):
    list_display = (
        "block_number",
        "block_hash",
        "previous_block_hash",
        "timestamp",
        "blockchain",
        "customer",
        "claim",
    )
    search_fields = ("block_number", "block_hash", "previous_block_hash")
    list_filter = ("blockchain",)


admin.site.register(Block, BlockAdmin)
admin.site.register(Blockchain, BlockchainAdmin)
admin.site.register(Claim, ClaimAdmin)
admin.site.register(Customer, CustomerAdmin)
admin.site.register(CoverageItem)
