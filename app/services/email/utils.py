# app/email_utils.py
import os
from fastapi_mail import FastMail, MessageSchema, MessageType
from app.services.email.config import conf
from pydantic import EmailStr

async def send_email_async(subject: str, recipient: str, body: str, attachment_path: str = None):
    message = MessageSchema(
        subject=subject,
        recipients=[recipient],
        body=body,
        subtype=MessageType.html,
        attachments=[attachment_path] if attachment_path else []
    )

    fm = FastMail(conf)
    await fm.send_message(message)