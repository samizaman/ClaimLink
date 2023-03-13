from django.shortcuts import render

from core.models import Claim


def claim_success(request):
    claim_id = request.session["claim_id"]
    claim = Claim.objects.get(id=claim_id)
    customer = claim.customer
    return render(request, "success.html", {"claim": claim, "customer": customer})
