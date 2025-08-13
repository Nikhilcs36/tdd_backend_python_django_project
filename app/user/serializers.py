from django.contrib.auth import get_user_model
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    """Serializer for the user object."""
    passwordRepeat = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = get_user_model()
        fields = ('username', 'email', 'password', 'passwordRepeat')
        extra_kwargs = {'password': {'write_only': True, 'min_length': 5}}

    def validate(self, attrs):
        """
        Validate that the password and passwordRepeat fields match.
        """
        if attrs['password'] != attrs['passwordRepeat']:
            raise serializers.ValidationError(
                {"password": "Password fields didn't match."}
            )
        return attrs

    def create(self, validated_data):
        """Create a new user with encrypted password and return it."""
        validated_data.pop('passwordRepeat')
        return get_user_model().objects.create_user(**validated_data)
