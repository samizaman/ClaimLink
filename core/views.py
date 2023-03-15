from django.shortcuts import redirect, render

from core.models import Claim, Customer


def personal_details(request):
    if request.method == "POST":
        if "next-claims-details" in request.POST:
            # Extract personal details from POST request
            name = request.POST.get("name")
            email = request.POST.get("email")
            phone_number = request.POST.get("phone_number", "")
            dob = request.POST.get("dob")
            gender = request.POST.get("gender")

            # Create new Customer instance and save to database
            customer = Customer(
                name=name,
                email=email,
                phone_number=phone_number,
                dob=dob,
                gender=gender,
            )
            customer.save()

            # Store customer ID in session
            request.session["customer_id"] = customer.id

            return redirect("claim_details")

    return render(request, "personal_details.html")


def claim_details(request):
    if request.method == "POST":
        if "submit-btn" in request.POST:
            # Extract claim details from POST request
            date_of_loss = request.POST.get("date_of_loss")
            description_of_loss = request.POST.get("description_of_loss")
            passport = request.FILES.get("passport")
            claim_amount = request.POST['claim_amount']

            # Get customer ID from session
            customer_id = request.session["customer_id"]

            # Create new Claim instance and save to database
            customer = Customer.objects.get(id=customer_id)

            claim = Claim(
                customer=customer,
                date_of_loss=date_of_loss,
                description_of_loss=description_of_loss,
                passport=passport,
                claim_amount=claim_amount,
            )
            claim.save()

            # Store claim ID in session
            request.session["claim_id"] = claim.id

            # Clear customer ID from session
            del request.session["customer_id"]

            return redirect("claim_success")

    return render(request, "claim_details.html")


def claim_success(request):
    claim_id = request.session["claim_id"]
    claim = Claim.objects.get(id=claim_id)
    customer = claim.customer
    return render(request, "success.html", {"claim": claim, "customer": customer})
