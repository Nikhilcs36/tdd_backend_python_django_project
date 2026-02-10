from django.utils import timezone
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, \
    PermissionsMixin


class UserManager(BaseUserManager):

    def create_user(self, username, email, password=None, **extra_fields):
        """Creates and saves a new user"""
        if not username:
            raise ValueError('Users must have a username')
        if not email:
            raise ValueError('Users must have an email address')
        user = self.model(
            username=username,
            email=self.normalize_email(email),
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, username, email, password):
        """Creates and saves a new superuser"""
        user = self.create_user(username, email, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)

        return user


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model that supports using username and email"""
    username = models.CharField(max_length=255, unique=True)
    email = models.EmailField(max_length=255, unique=True, error_messages={
        'unique': 'E-mail in use'
    })
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    image = models.ImageField(upload_to='uploads/user/', null=True, blank=True)
    # Login statistics fields
    login_count = models.PositiveIntegerField(default=0)
    last_login_timestamp = models.DateTimeField(null=True, blank=True)
    weekly_logins = models.JSONField(default=dict, blank=True)
    monthly_logins = models.JSONField(default=dict, blank=True)
    # Email verification fields
    email_verified = models.BooleanField(default=False)
    verification_token = models.CharField(
        max_length=100, blank=True, null=True)
    verification_token_created_at = models.DateTimeField(null=True, blank=True)
    password_reset_token = models.CharField(
        max_length=100, blank=True, null=True)
    password_reset_token_created_at = models.DateTimeField(
        null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        ordering = ['id']

    def delete(self, *args, **kwargs):
        """
        Override the delete method to ensure the associated image
        file is deleted when a user is deleted.
        """
        if self.image:
            # Ensure the image file exists before trying to delete it
            if self.image.storage.exists(self.image.name):
                self.image.storage.delete(self.image.name)
        super().delete(*args, **kwargs)

    def generate_verification_token(self):
        """Generate a verification token for email verification"""
        import secrets
        self.verification_token = secrets.token_urlsafe(32)
        self.verification_token_created_at = timezone.now()
        self.save()
        return self.verification_token

    def verify_email(self, token):
        """Verify email with token"""
        if self.verification_token == token:
            self.email_verified = True
            self.verification_token = None
            self.verification_token_created_at = None
            self.save()
            return True
        return False

    def is_verification_token_expired(self):
        """Check if verification token is expired (24 hours)"""
        if not self.verification_token_created_at:
            return True
        from datetime import timedelta
        expiration_time = self.verification_token_created_at + \
            timedelta(hours=24)
        return timezone.now() > expiration_time

    def generate_password_reset_token(self):
        """Generate a password reset token"""
        import secrets
        self.password_reset_token = secrets.token_urlsafe(32)
        self.password_reset_token_created_at = timezone.now()
        self.save()
        return self.password_reset_token

    def is_password_reset_token_expired(self):
        """Check if password reset token is expired (1 hour)"""
        if not self.password_reset_token_created_at:
            return True
        from datetime import timedelta
        expiration_time = self.password_reset_token_created_at + \
            timedelta(hours=1)
        return timezone.now() > expiration_time

    def reset_password(self, token, new_password):
        """Reset password with token"""
        if (self.password_reset_token == token and
                not self.is_password_reset_token_expired()):
            self.set_password(new_password)
            self.password_reset_token = None
            self.password_reset_token_created_at = None
            self.save()
            return True
        return False


class LoginActivity(models.Model):
    """Model to track user login activities"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='login_activities'
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.CharField(max_length=500)
    success = models.BooleanField(default=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Login Activity'
        verbose_name_plural = 'Login Activities'

    def __str__(self):
        return f"LoginActivity for {self.user.username} at {self.timestamp}"

    def save(self, *args, **kwargs):
        """Override save to update user statistics on successful login"""
        is_new = self.pk is None

        # Call the parent save method first to ensure the object is saved
        super().save(*args, **kwargs)

        # Only update user statistics for successful logins
        if is_new and self.success:
            # Update user login count
            self.user.login_count = models.F('login_count') + 1
            # Update last login timestamp
            self.user.last_login_timestamp = self.timestamp

            # Update weekly and monthly login statistics
            from django.utils import timezone
            from datetime import timedelta

            current_time = timezone.now()

            # Update weekly logins
            week_start = current_time - timedelta(days=current_time.weekday())
            week_key = week_start.strftime('%Y-%U')
            weekly_data = self.user.weekly_logins or {}
            weekly_data[week_key] = weekly_data.get(week_key, 0) + 1
            self.user.weekly_logins = weekly_data

            # Update monthly logins
            month_key = current_time.strftime('%Y-%m')
            monthly_data = self.user.monthly_logins or {}
            monthly_data[month_key] = monthly_data.get(month_key, 0) + 1
            self.user.monthly_logins = monthly_data

            # Save the updated user
            self.user.save()
