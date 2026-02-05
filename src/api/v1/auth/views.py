"""Views for authentication API.

Handles user registration, login, logout, and password management.
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth import get_user_model
from django.utils.decorators import method_decorator
# from django_ratelimit.decorators import ratelimit  # DISABLED FOR TESTING

from .serializers import (
    RegisterSerializer,
    CustomTokenObtainPairSerializer,
    ChangePasswordSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
)

User = get_user_model()


# @method_decorator(ratelimit(key='ip', rate='5/m', method='POST'), name='dispatch')  # DISABLED FOR TESTING
class RegisterView(APIView):
    """API view for user registration.
    
    Creates new user account and returns JWT tokens.
    Rate limiting DISABLED for testing.
    """
    
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Register new user.
        
        Request Body:
            email (str): Email address
            phone (str): Phone number
            first_name (str): First name
            last_name (str): Last name
            password (str): Password
            password2 (str): Password confirmation
        
        Returns:
            Response: User data and JWT tokens
        """
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.save()
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': {
                'id': str(user.public_id),
                'email': user.email,
                'phone': user.phone,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'full_name': user.get_full_name(),
            },
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)


# @method_decorator(ratelimit(key='ip', rate='10/m', method='POST'), name='dispatch')  # DISABLED FOR TESTING
class LoginView(TokenObtainPairView):
    """API view for user login.
    
    Returns JWT tokens and user data.
    Rate limiting DISABLED for testing.
    """
    
    serializer_class = CustomTokenObtainPairSerializer


class LogoutView(APIView):
    """API view for user logout.
    
    Blacklists the refresh token.
    """
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Logout user by blacklisting refresh token.
        
        Request Body:
            refresh (str): Refresh token to blacklist
        
        Returns:
            Response: Success message
        """
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response(
                    {'error': 'Refresh token is required.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            return Response(
                {'message': 'Successfully logged out.'},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class ChangePasswordView(APIView):
    """API view for password change.
    
    Requires authentication and old password.
    """
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Change user password.
        
        Request Body:
            old_password (str): Current password
            new_password (str): New password
            new_password2 (str): New password confirmation
        
        Returns:
            Response: Success message
        """
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        # Set new password
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        
        return Response(
            {'message': 'Password changed successfully.'},
            status=status.HTTP_200_OK
        )


# @method_decorator(ratelimit(key='ip', rate='5/h', method='POST'), name='dispatch')  # DISABLED FOR TESTING
class PasswordResetRequestView(APIView):
    """API view for password reset request.
    
    Sends password reset email with token.
    Rate limiting DISABLED for testing.
    """
    
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Request password reset.
        
        Request Body:
            email (str): User email address
        
        Returns:
            Response: Success message
        """
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        user = User.objects.get(email=email)
        
        # Generate reset token
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        # In production, send email with reset link
        # For now, return token in response (development only)
        reset_link = f"https://yoursite.com/reset-password?uid={uid}&token={token}"
        
        # TODO: Send email in Phase 12 (Notifications)
        # EmailService.send_password_reset_email(user, reset_link)
        
        return Response({
            'message': 'Password reset link has been sent to your email.',
            # Development only - remove in production
            'dev_reset_link': reset_link,
            'dev_token': token,
            'dev_uid': uid,
        }, status=status.HTTP_200_OK)


class PasswordResetConfirmView(APIView):
    """API view for password reset confirmation.
    
    Validates token and sets new password.
    """
    
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Confirm password reset.
        
        Request Body:
            uid (str): User ID (base64 encoded)
            token (str): Reset token
            new_password (str): New password
            new_password2 (str): New password confirmation
        
        Returns:
            Response: Success message
        """
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        uid = request.data.get('uid')
        token = serializer.validated_data['token']
        
        try:
            # Decode user ID
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
            
            # Validate token
            if not default_token_generator.check_token(user, token):
                return Response(
                    {'error': 'Invalid or expired reset token.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Set new password
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            return Response(
                {'message': 'Password reset successfully.'},
                status=status.HTTP_200_OK
            )
            
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response(
                {'error': 'Invalid reset link.'},
                status=status.HTTP_400_BAD_REQUEST
            )
