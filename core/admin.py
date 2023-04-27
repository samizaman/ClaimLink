from django.contrib import admin

from .models import Block, Blockchain, Claim, CoverageItem, Customer


class ClaimAdmin(admin.ModelAdmin):
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


class CustomerAdmin(admin.ModelAdmin):
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


class BlockAdmin(admin.ModelAdmin):
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
