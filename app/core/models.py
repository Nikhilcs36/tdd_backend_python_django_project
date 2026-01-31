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


class LoginActivity(models.Model):
    """Model to track user login activities"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='login_activities',
        null=True,
        blank=True
    )
    attempted_username = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Username/email attempted during login (for failed login attempts)"
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
        username = self.user.username if self.user else self.attempted_username or 'Unknown'
        return f"LoginActivity for {username} at {self.timestamp}"

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
