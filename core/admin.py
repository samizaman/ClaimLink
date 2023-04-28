import csv

from django.contrib import admin
from django.http import HttpResponse
from django.urls import path

from .models import Block, Blockchain, Claim, CoverageItem, Customer


class ExportCsvMixin:
    """
    Mixin to provide CSV export functionality for Django admin models.
    This mixin includes two methods: export_as_csv() and export_all_as_csv().
    export_as_csv() exports selected objects in the admin interface as a CSV file,
    while export_all_as_csv() exports all objects of a model as a CSV file.
    """

    def export_as_csv(self, request, queryset):
        """
        Exports selected objects from a queryset as a CSV file.

        Args:
            request (HttpRequest): The request from the admin interface.
            queryset (QuerySet): A queryset containing the selected objects to export.

        Returns:
            HttpResponse: A response containing the CSV file.
        """
        # Get the model's metadata
        meta = self.model._meta
        # Get field names from the metadata
        field_names = [field.name for field in meta.fields]
        # Initialize an HTTP response with content type set to text/csv
        response = HttpResponse(content_type="text/csv")
        # Set content disposition header to define the filename
        response["Content-Disposition"] = f"attachment; filename={meta}.csv"
        # Create a CSV writer object
        writer = csv.writer(response)
        # Write the header row with field names
        writer.writerow(field_names)
        # Iterate through the queryset and write each object's data as a row in the CSV
        for obj in queryset.all():
            row = writer.writerow([getattr(obj, field) for field in field_names])
        return response

    # Set the short description for the export_as_csv action
    export_as_csv.short_description = "Export Selected as CSV"

    def export_all_as_csv(self, request):
        """
        Exports all objects of a model as a CSV file.

        Args:
            request (HttpRequest): The request from the admin interface.

        Returns:
            HttpResponse: A response containing the CSV file.
        """
        # Get all objects of the model
        queryset = self.model.objects.all()
        # Call export_as_csv with the queryset containing all objects
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
