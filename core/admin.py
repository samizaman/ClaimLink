import json

from django.contrib import admin
from django.http import HttpResponse

from .models import Block, Blockchain, Claim, CoverageItem, Customer
from .views import get_claim_data_from_blockchain


def view_claim_data_on_blockchain(modeladmin, request, queryset):
    # Assuming each claim has a unique input_data_hex
    input_data_hex = queryset.first().input_data_hex
    claim_data = get_claim_data_from_blockchain(input_data_hex)

    if claim_data:
        claim_data = json.dumps(claim_data, indent=4)
        return HttpResponse("<pre>" + claim_data + "</pre>")
    else:
        return HttpResponse("Error: Could not retrieve claim data from the blockchain.")


view_claim_data_on_blockchain.short_description = "View Claim Data on Blockchain"


class ClaimAdmin(admin.ModelAdmin):
    list_display = (
        "claim_reference_number",
        "customer",
        "id",
        "date_of_loss",
        "timestamp",
    )
    list_filter = ("date_of_loss", "timestamp")
    ordering = ("-timestamp",)
    actions = [view_claim_data_on_blockchain]


class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone_number", "dob", "gender", "timestamp")
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
    )
    search_fields = ("block_number", "block_hash", "previous_block_hash")
    list_filter = ("blockchain",)


admin.site.register(Block, BlockAdmin)
admin.site.register(Blockchain, BlockchainAdmin)
admin.site.register(Claim, ClaimAdmin)
admin.site.register(Customer, CustomerAdmin)
admin.site.register(CoverageItem)
