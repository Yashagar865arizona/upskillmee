from pydantic import BaseModel, EmailStr, constr
from typing import Optional

class SendOtpRequest(BaseModel):
    email: Optional[EmailStr] = None
    phone_number: Optional[constr(min_length=8, max_length=15)] = None

    def validate_input(self):
        if not self.email and not self.phone_number:
            raise ValueError("Either email or phone_number must be provided")


class VerifyOtpRequest(BaseModel):
    email: Optional[EmailStr] = None
    phone_number: Optional[constr(min_length=8, max_length=15)] = None
    otp: constr(min_length=4, max_length=6)

    def validate_input(self):
        if not self.email and not self.phone_number:
            raise ValueError("Either email or phone_number must be provided")
