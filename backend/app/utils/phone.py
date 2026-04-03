import phonenumbers

def format_phone_number(number: str, default_region="IN") -> str:
    try:
        parsed_number = phonenumbers.parse(number, default_region)
        if not phonenumbers.is_valid_number(parsed_number):
            raise ValueError("Invalid phone number")
        return phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
    except Exception as e:
        raise ValueError(f"Invalid phone number format: {e}")
