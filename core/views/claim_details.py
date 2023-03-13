from django.shortcuts import redirect, render

from core.models import Claim, Customer


def claim_details(request):
    if request.method == "POST":
        if "submit-btn" in request.POST:
            # Extract claim details from POST request
            date_of_loss = request.POST.get("date_of_loss")
            description_of_loss = request.POST.get("description_of_loss")
            passport = request.FILES.get("passport")

            # Get customer ID from session
            customer_id = request.session["customer_id"]

            # Create new Claim instance and save to database
            customer = Customer.objects.get(id=customer_id)

            claim = Claim(
                customer=customer,
                date_of_loss=date_of_loss,
                description_of_loss=description_of_loss,
                passport=passport,
            )
            claim.save()

            # Store claim ID in session
            request.session["claim_id"] = claim.id

            # Clear customer ID from session
            del request.session["customer_id"]

            return redirect("claim_success")

    return render(request, "claim_details.html")
