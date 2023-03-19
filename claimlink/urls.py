from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from core.views import (
    claim_details,
    claim_success,
    claim_summary,
    coverage_items_selection,
    home,
    personal_details,
    required_documents,
    view_claim,
)

urlpatterns = [
    path("", home, name="home"),
    path("personal-details/", personal_details, name="personal_details"),
    path("claim-details/", claim_details, name="claim_details"),
    path("success/", claim_success, name="claim_success"),
    path("view-claim/", view_claim, name="view_claim"),
    path("coverage-items-selection/",coverage_items_selection,name="coverage_items_selection"),
    path("required-documents/", required_documents, name="required_documents"),
    path("claim-summary/", claim_summary, name="claim_summary"),
    path("admin/", admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
