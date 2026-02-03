"""
Custom security middleware for additional protection.

Provides request logging and suspicious activity detection.
"""

import logging
from django.http import HttpResponseForbidden
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class SecurityLoggingMiddleware(MiddlewareMixin):
    """
    Log security-relevant events.
    
    Logs failed authentication attempts, suspicious requests,
    and other security events.
    """
    
    def process_request(self, request):
        """Log incoming request details."""
        # Log authentication attempts
        if request.path in ['/api/v1/auth/login/', '/api/v1/auth/register/']:
            logger.info(
                f"Auth attempt: {request.method} {request.path} from {self.get_client_ip(request)}"
            )
        
        return None
    
    def process_response(self, request, response):
        """Log security-relevant responses."""
        # Log failed authentication
        if request.path in ['/api/v1/auth/login/', '/api/v1/auth/register/']:
            if response.status_code >= 400:
                logger.warning(
                    f"Failed auth: {request.method} {request.path} - "
                    f"Status {response.status_code} from {self.get_client_ip(request)}"
                )
        
        # Log admin access
        if request.path.startswith('/admin/') and request.user.is_authenticated:
            if request.user.is_staff:
                logger.info(
                    f"Admin access: {request.user.email} - {request.method} {request.path}"
                )
        
        return response
    
    @staticmethod
    def get_client_ip(request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SuspiciousRequestMiddleware(MiddlewareMixin):
    """
    Detect and block suspicious requests.
    
    Blocks requests with suspicious patterns that might
    indicate attacks.
    """
    
    # Suspicious patterns in URLs
    SUSPICIOUS_PATTERNS = [
        '<script',
        'javascript:',
        'onerror=',
        'onclick=',
        '../',
        '..\\',
        'union select',
        'drop table',
        'insert into',
        'delete from',
    ]
    
    def process_request(self, request):
        """Check for suspicious patterns."""
        # Check URL path
        path_lower = request.path.lower()
        
        for pattern in self.SUSPICIOUS_PATTERNS:
            if pattern in path_lower:
                logger.error(
                    f"Suspicious request blocked: {request.path} from "
                    f"{SecurityLoggingMiddleware.get_client_ip(request)}"
                )
                return HttpResponseForbidden("Suspicious request detected")
        
        # Check query parameters
        for key, value in request.GET.items():
            value_lower = str(value).lower()
            for pattern in self.SUSPICIOUS_PATTERNS:
                if pattern in value_lower:
                    logger.error(
                        f"Suspicious query parameter: {key}={value} from "
                        f"{SecurityLoggingMiddleware.get_client_ip(request)}"
                    )
                    return HttpResponseForbidden("Suspicious request detected")
        
        return None


class AdminIPWhitelistMiddleware(MiddlewareMixin):
    """
    Optional: Restrict admin access to specific IP addresses.
    
    Enable in production by adding to MIDDLEWARE and setting
    ADMIN_ALLOWED_IPS in settings.
    """
    
    def process_request(self, request):
        """Check if admin access from allowed IP."""
        from django.conf import settings
        
        # Only check admin paths
        if not request.path.startswith('/admin/'):
            return None
        
        # Get allowed IPs from settings (if configured)
        allowed_ips = getattr(settings, 'ADMIN_ALLOWED_IPS', None)
        
        # If not configured, allow all (disabled)
        if not allowed_ips:
            return None
        
        # Get client IP
        client_ip = SecurityLoggingMiddleware.get_client_ip(request)
        
        # Check if IP allowed
        if client_ip not in allowed_ips:
            logger.warning(
                f"Admin access denied for IP: {client_ip} - Path: {request.path}"
            )
            return HttpResponseForbidden(
                "Access to admin panel is restricted."
            )
        
        return None
