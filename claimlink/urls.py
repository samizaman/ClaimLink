from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from core.views import claim_details, claim_success, personal_details

urlpatterns = [
    path("", personal_details, name="personal_details"),
    path("claim-details/", claim_details, name="claim_details"),
    path("success/", claim_success, name="claim_success"),
    path("admin/", admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
