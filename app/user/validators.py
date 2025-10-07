import re
from django.contrib.auth import get_user_model
from rest_framework import serializers

# Custom validator for username


def validate_username(value):
    """
    Validates that the username is not null and is between 4 and 32 characters.
    """
    if not value:
        raise serializers.ValidationError("Username is required.")
    if len(value) < 4 or len(value) > 32:
        raise serializers.ValidationError(
            "Must have min 4 and max 32 characters")
    return value

# Custom validator for email during signup


def validate_email_for_signup(value):
    """
    Validates that the email is not null, is a valid format,
    and is not already in use.
    """
    if not value:
        raise serializers.ValidationError("Email is required.")
    if not re.match(r"[^@]+@[^@]+\.[^@]+", value):
        raise serializers.ValidationError(
            "Enter a valid email (e.g., user@example.com).")
    if get_user_model().objects.filter(email=value).exists():
        raise serializers.ValidationError("Email is already in use.")
    return value

# Custom validator for password


def validate_password(value):
    """
    Validates that the password is not null, is at least 6 characters long,
    and contains at least one uppercase letter, one lowercase letter,
    and one number.
    """
    if not value:
        raise serializers.ValidationError("Password cannot be null")
    if len(value) < 6:
        raise serializers.ValidationError(
            "Password must have at least 6 characters")
    if not re.search(r"[a-z]", value) or \
       not re.search(r"[A-Z]", value) or \
       not re.search(r"\d", value):
        raise serializers.ValidationError(
            "Password must have at least 1 uppercase, "
            "1 lowercase letter and 1 number"
        )
    return value
