import re

from flask import current_app, url_for
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer
from wtforms.validators import ValidationError

from extensions import mail


def generate_reset_token(email):
    serializer = URLSafeTimedSerializer(
        current_app.config["SECRET_KEY"]
    )

    return serializer.dumps(
        email,
        salt="password-reset-salt"
    )


def verify_reset_token(token, max_age=3600):
    serializer = URLSafeTimedSerializer(
        current_app.config["SECRET_KEY"]
    )

    try:
        email = serializer.loads(
            token,
            salt="password-reset-salt",
            max_age=max_age
        )
        return email

    except Exception:
        return None


def strong_password(form, field):
    password = field.data

    if len(password) < 8:
        raise ValidationError(
            "Password must be at least 8 characters long."
        )

    if not re.search(r"[A-Z]", password):
        raise ValidationError(
            "Password must contain at least one uppercase letter."
        )

    if not re.search(r"[a-z]", password):
        raise ValidationError(
            "Password must contain at least one lowercase letter."
        )

    if not re.search(r"\d", password):
        raise ValidationError(
            "Password must contain at least one number."
        )

    if not re.search(r"[^A-Za-z0-9]", password):
        raise ValidationError(
            "Password must contain at least one special character."
        )


def is_strong_password(password):
    if len(password) < 8:
        return False

    if not re.search(r"[A-Z]", password):
        return False

    if not re.search(r"[a-z]", password):
        return False

    if not re.search(r"\d", password):
        return False

    if not re.search(r"[^A-Za-z0-9]", password):
        return False

    return True


def send_reset_email(user):
    token = generate_reset_token(user.email)

    reset_url = url_for(
        "reset_password",
        token=token,
        _external=True
    )

    msg = Message(
        subject="Reset Your Password",
        recipients=[user.email]
    )

    msg.body = f"""
Hello {user.username},

To reset your password, visit:

{reset_url}

This link expires in 1 hour.
"""

    try:
        mail.send(msg)
        print("EMAIL SENT SUCCESSFULLY")
    except Exception as e:
        print("MAIL ERROR:", str(e))
        raise
