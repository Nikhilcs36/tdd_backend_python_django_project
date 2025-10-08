from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from .validators import (
    validate_username,
    validate_email_for_signup,
    validate_password
)


class UserSerializer(serializers.ModelSerializer):
    """Serializer for the user object."""
    passwordRepeat = serializers.CharField(
        write_only=True,
        required=False,
        style={'input_type': 'password'},
        error_messages={'blank': 'password_repeat_null'}
    )
    image = serializers.FileField(
        max_length=100,
        allow_empty_file=True,
        use_url=True,
        required=False,
        allow_null=True
    )

    class Meta:
        model = get_user_model()
        fields = ('id', 'username', 'email', 'password',
                  'passwordRepeat', 'image')
        extra_kwargs = {
            'password': {
                'write_only': True, 'validators': [validate_password],
                'error_messages': {
                    'blank': 'Password cannot be null',
                }
            },
            'username': {
                'validators': [validate_username],
                'error_messages': {
                    'blank': 'Username cannot be null',
                    'unique': 'Username already exists',
                }
            },
            'email': {
                'error_messages': {
                    'blank': 'E-mail cannot be null',
                    'invalid': 'E-mail is not valid',
                    'unique': 'E-mail in use',
                }
            },
        }

    def validate(self, attrs):
        """
        Validate that the password and passwordRepeat fields match.
        """
        password = attrs.get('password')
        password_repeat = attrs.get('passwordRepeat')

        # On creation, both password and passwordRepeat are required
        if not self.instance:
            if not password_repeat:
                raise serializers.ValidationError(
                    {"passwordRepeat": "password_repeat_null"}
                )
            if password != password_repeat:
                msg = {"passwordRepeat": "password_mismatch"}
                raise serializers.ValidationError(msg)
        # On update, if password is provided, passwordRepeat must also be
        # provided
        elif password:
            if not password_repeat:
                raise serializers.ValidationError(
                    {"passwordRepeat": "password_repeat_null"}
                )
            if password != password_repeat:
                msg = {"passwordRepeat": "password_mismatch"}
                raise serializers.ValidationError(msg)
        return attrs

    def create(self, validated_data):
        """Create a new user with encrypted password and return it."""
        if 'passwordRepeat' in validated_data:
            validated_data.pop('passwordRepeat')
        return get_user_model().objects.create_user(**validated_data)

    def __init__(self, *args, **kwargs):
        """
        Dynamically set email to read-only for updates and apply email
        validator only for create operations.
        """
        super().__init__(*args, **kwargs)
        if self.instance:
            self.fields['email'].read_only = True
        else:
            # Remove Django's built-in email validation to avoid duplicate
            # errors since validate_email_for_signup already handles all
            # email validation
            self.fields['email'].validators = [validate_email_for_signup]

    def update(self, instance, validated_data):
        """Update a user, setting the password correctly and return it."""
        password = validated_data.pop('password', None)

        # Handle clearing the image.
        # An empty string from multipart form data indicates clearing the image
        if validated_data.get('image') == '':
            validated_data['image'] = None

        # Delete old image file if it exists and the image field is being
        # updated (either with a new image or by clearing it)
        if instance.image and 'image' in validated_data:
            instance.image.delete(save=False)  # Delete old file from storage

        user = super().update(instance, validated_data)

        if password:
            user.set_password(password)
            user.save()

        return user

    def validate_image(self, value):
        """
        Check that the uploaded file is a valid image (JPG, JPEG, or PNG)
        and that its size is within the allowed limit.
        """
        if not value:
            return value

        # Check file extension
        allowed_extensions = ['jpg', 'jpeg', 'png']
        extension = value.name.split('.')[-1].lower()
        if extension not in allowed_extensions:
            raise serializers.ValidationError(
                'Invalid image format. Only JPG, JPEG, and PNG are allowed.'
            )

        # Check file size
        if value.size > settings.MAX_UPLOAD_SIZE:
            raise serializers.ValidationError(
                f'Image size cannot exceed {settings.MAX_UPLOAD_SIZE} bytes.'
            )

        return value


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom serializer for token obtain pair view."""

    default_error_messages = {
        'no_active_account': 'no_active_account'
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'] = serializers.EmailField(
            error_messages={
                'blank': 'email_required',
                'invalid': 'email_invalid',
            }
        )
        self.fields['password'] = serializers.CharField(
            style={'input_type': 'password'},
            trim_whitespace=False,
            error_messages={
                'blank': 'password_required',
            }
        )
        del self.fields['username']

    def validate(self, attrs):
        """
        Validate the user's credentials and return a token pair.
        """
        # The default result (access/refresh tokens)
        user = authenticate(
            request=self.context.get('request'),
            username=attrs.get('email'),
            password=attrs.get('password')
        )

        if not user:
            self.fail('no_active_account')

        refresh = self.get_token(user)

        data = {}
        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)

        # Add custom data to the response
        data.update({'id': user.id})
        data.update({'username': user.username})
        data.update({'email': user.email})
        return data


class LogoutSerializer(serializers.Serializer):
    """Serializer for the logout endpoint."""
    refresh = serializers.CharField()

    default_error_messages = {
        'bad_token': ('Token is expired or invalid')
    }

    def validate(self, attrs):
        self.token = attrs['refresh']
        return attrs

    def save(self, **kwargs):
        try:
            RefreshToken(self.token).blacklist()
        except TokenError:
            self.fail('bad_token')
