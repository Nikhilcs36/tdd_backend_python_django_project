"""Email service for sending verification and password reset emails."""
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings


def send_verification_email(user, verification_url):
    """Send email verification email to user.

    Args:
        user: User instance
        verification_url: The verification URL to include in the email
    """
    subject = 'Verify your email address'
    html_message = render_to_string('email/verification_email.html', {
        'user': user,
        'verification_url': verification_url,
    })
    plain_message = strip_tags(html_message)

    send_mail(
        subject=subject,
        message=plain_message,
        html_message=html_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )


def send_password_reset_email(user, reset_url):
    """Send password reset email to user.

    Args:
        user: User instance
        reset_url: The password reset URL to include in the email
    """
    subject = 'Reset your password'
    html_message = render_to_string('email/password_reset.html', {
        'user': user,
        'reset_url': reset_url,
    })
    plain_message = strip_tags(html_message)

    send_mail(
        subject=subject,
        message=plain_message,
        html_message=html_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )


def build_verification_url(request, token):
    """Build verification URL for email verification.

    Args:
        request: HttpRequest object
        token: Verification token

    Returns:
        str: Full verification URL
    """
    if request:
        base_url = request.build_absolute_uri('/')
    else:
        base_url = 'http://localhost:8000/'

    # Remove trailing slash if present
    base_url = base_url.rstrip('/')
    return f"{base_url}/api/user/verify-email/{token}/"


def build_password_reset_url(request, token):
    """Build password reset URL.

    Args:
        request: HttpRequest object
        token: Password reset token

    Returns:
        str: Full password reset URL
    """
    if request:
        base_url = request.build_absolute_uri('/')
    else:
        base_url = 'http://localhost:8000/'

    # Remove trailing slash if present
    base_url = base_url.rstrip('/')
    return f"{base_url}/api/user/reset-password/{token}/"


def send_welcome_email(user):
    """Send welcome email after successful verification.

    Args:
        user: User instance
    """
    subject = 'Welcome to our platform!'
    html_message = render_to_string('email/welcome_email.html', {
        'user': user,
    })
    plain_message = strip_tags(html_message)

    send_mail(
        subject=subject,
        message=plain_message,
        html_message=html_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )
