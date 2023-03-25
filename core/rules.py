def check_passport_rules(response, name):
    violated_rules = []

    # Check name mismatch rule
    extracted_name = response.get("result", {}).get("fullName", "")  # Get the full name from the response
    if extracted_name:
        extracted_name = (
            extracted_name.lower()
        )  # Convert the extracted name to lowercase
    user_name = name.lower()  # Convert the user-provided name to lowercase

    print(f"Extracted name from passport: {extracted_name}")
    print(f"Name provided by user: {user_name}")

    if extracted_name and user_name != extracted_name:
        violated_rules.append("name_mismatch")

    # Add more rules here as needed

    return violated_rules
