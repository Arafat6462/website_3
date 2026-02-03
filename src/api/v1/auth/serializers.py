"""Serializers for authentication API.

Handles user registration, login, and password management.
"""

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration.
    
    Creates new user account with email and password.
    """
    
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password2 = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        label='Confirm Password'
    )
    
    class Meta:
        model = User
        fields = [
            'email',
            'phone',
            'first_name',
            'last_name',
            'password',
            'password2',
        ]
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'phone': {'required': True},
        }
    
    def validate_email(self, value):
        """Validate email is unique.
        
        Args:
            value (str): Email address
        
        Returns:
            str: Validated email
        
        Raises:
            ValidationError: If email already exists
        """
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()
    
    def validate_phone(self, value):
        """Validate phone is unique.
        
        Args:
            value (str): Phone number
        
        Returns:
            str: Validated phone
        
        Raises:
            ValidationError: If phone already exists
        """
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("A user with this phone number already exists.")
        return value
    
    def validate(self, data):
        """Validate passwords match.
        
        Args:
            data (dict): Validated data
        
        Returns:
            dict: Validated data
        
        Raises:
            ValidationError: If passwords don't match
        """
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password2": "Passwords do not match."})
        return data
    
    def create(self, validated_data):
        """Create new user.
        
        Args:
            validated_data (dict): Validated data
        
        Returns:
            User: Created user instance
        """
        validated_data.pop('password2')
        user = User.objects.create_user(
            email=validated_data['email'],
            phone=validated_data['phone'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            password=validated_data['password']
        )
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT token serializer with user data.
    
    Returns access and refresh tokens plus user info.
    """
    
    @classmethod
    def get_token(cls, user):
        """Add custom claims to token.
        
        Args:
            user (User): User instance
        
        Returns:
            Token: JWT token with claims
        """
        token = super().get_token(user)
        
        # Add custom claims
        token['email'] = user.email
        token['name'] = user.get_full_name()
        
        return token
    
    def validate(self, attrs):
        """Validate and return tokens with user data.
        
        Args:
            attrs (dict): Login credentials
        
        Returns:
            dict: Tokens and user data
        """
        data = super().validate(attrs)
        
        # Add user data to response
        data['user'] = {
            'id': str(self.user.public_id),
            'email': self.user.email,
            'phone': self.user.phone,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'full_name': self.user.get_full_name(),
        }
        
        return data


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password change.
    
    Requires old password and validates new password.
    """
    
    old_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    new_password2 = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
        label='Confirm New Password'
    )
    
    def validate_old_password(self, value):
        """Validate old password is correct.
        
        Args:
            value (str): Old password
        
        Returns:
            str: Validated password
        
        Raises:
            ValidationError: If old password incorrect
        """
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value
    
    def validate(self, data):
        """Validate new passwords match.
        
        Args:
            data (dict): Validated data
        
        Returns:
            dict: Validated data
        
        Raises:
            ValidationError: If passwords don't match
        """
        if data['new_password'] != data['new_password2']:
            raise serializers.ValidationError({"new_password2": "New passwords do not match."})
        return data


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for password reset request.
    
    Sends password reset email to user.
    """
    
    email = serializers.EmailField(required=True)
    
    def validate_email(self, value):
        """Validate email exists.
        
        Args:
            value (str): Email address
        
        Returns:
            str: Validated email
        
        Raises:
            ValidationError: If email not found
        """
        if not User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError("No user found with this email address.")
        return value.lower()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for password reset confirmation.
    
    Validates token and sets new password.
    """
    
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    new_password2 = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
        label='Confirm New Password'
    )
    
    def validate(self, data):
        """Validate new passwords match.
        
        Args:
            data (dict): Validated data
        
        Returns:
            dict: Validated data
        
        Raises:
            ValidationError: If passwords don't match
        """
        if data['new_password'] != data['new_password2']:
            raise serializers.ValidationError({"new_password2": "Passwords do not match."})
        return data
