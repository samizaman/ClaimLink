from django.contrib import admin

from .models import Block, Blockchain, Claim, Customer


class ClaimAdmin(admin.ModelAdmin):
    list_display = ("customer", "id", "date_of_loss", "timestamp")
    list_filter = ("date_of_loss", "timestamp")
    ordering = ("-timestamp",)


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
