from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


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


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom serializer for token obtain pair view."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'] = serializers.EmailField()
        self.fields['password'] = serializers.CharField(
            style={'input_type': 'password'},
            trim_whitespace=False
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
            raise serializers.ValidationError(
                'No active account found with the given credentials'
            )

        refresh = self.get_token(user)

        data = {}
        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)

        # Add custom data to the response
        data.update({'username': user.username})
        data.update({'email': user.email})
        return data
