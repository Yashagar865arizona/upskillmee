from sqlalchemy.orm import Session, object_session
from sqlalchemy import event
import asyncio
import os
from app.services.email_service import send_verification_email
from app.models.user import PendingUserEmail
from app.config.settings import settings

def after_update_listener(mapper, connection, target: PendingUserEmail):
    session = object_session(target)
   
    if target.is_verified_by_admin and not target.email_sent:
        target.email_sent = True
        session.commit()
        # schedule async email
        asyncio.create_task(send_verification_email(target.email, settings.WEBSITE_URL))

event.listen(PendingUserEmail, "after_update", after_update_listener)
