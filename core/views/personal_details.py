from django.shortcuts import redirect, render

from core.models import Customer


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
