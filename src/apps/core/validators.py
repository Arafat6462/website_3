"""
Security utilities for input validation and sanitization.

This module provides validators and sanitizers to prevent
XSS, SQL injection, and other security vulnerabilities.
"""

import re
from typing import List, Optional
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator, RegexValidator


class BangladeshiPhoneValidator(RegexValidator):
    """
    Validator for Bangladeshi phone numbers.
    
    Accepts formats:
    - 01712345678 (11 digits, starts with 01)
    - +8801712345678 (with country code)
    - 8801712345678 (without +)
    """
    
    regex = r'^(\+?880|0)?1[3-9]\d{8}$'
    message = 'Enter a valid Bangladeshi phone number (e.g., 01712345678)'
    code = 'invalid_phone'


def validate_file_extension(value, allowed_extensions: List[str]):
    """
    Validate file extension.
    
    Args:
        value: File upload object
        allowed_extensions: List of allowed extensions (e.g., ['jpg', 'png'])
        
    Raises:
        ValidationError: If file extension not allowed
    """
    import os
    ext = os.path.splitext(value.name)[1].lower().strip('.')
    
    if ext not in allowed_extensions:
        raise ValidationError(
            f'File type not allowed. Allowed types: {", ".join(allowed_extensions)}'
        )


def validate_file_size(value, max_size_mb: int = 5):
    """
    Validate file size.
    
    Args:
        value: File upload object
        max_size_mb: Maximum size in megabytes
        
    Raises:
        ValidationError: If file too large
    """
    max_size_bytes = max_size_mb * 1024 * 1024
    
    if value.size > max_size_bytes:
        raise ValidationError(
            f'File size must be under {max_size_mb}MB. Current size: {value.size / (1024*1024):.2f}MB'
        )


def validate_image_file(value):
    """
    Validate image file (extension and size).
    
    Args:
        value: File upload object
        
    Raises:
        ValidationError: If file not valid image
    """
    allowed_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp']
    validate_file_extension(value, allowed_extensions)
    validate_file_size(value, max_size_mb=5)


def sanitize_html(text: str) -> str:
    """
    Remove HTML tags from text to prevent XSS.
    
    Args:
        text: Input text that may contain HTML
        
    Returns:
        str: Sanitized text with HTML removed
    """
    import html
    # Escape HTML entities
    text = html.escape(text)
    # Remove any remaining tags
    text = re.sub(r'<[^>]*>', '', text)
    return text


def sanitize_phone_number(phone: str) -> str:
    """
    Normalize Bangladeshi phone number.
    
    Args:
        phone: Phone number in various formats
        
    Returns:
        str: Normalized phone number (11 digits starting with 0)
        
    Examples:
        +8801712345678 -> 01712345678
        8801712345678 -> 01712345678
        01712345678 -> 01712345678
    """
    # Remove all non-digit characters
    phone = re.sub(r'\D', '', phone)
    
    # Remove country code if present
    if phone.startswith('880'):
        phone = '0' + phone[3:]
    
    # Ensure starts with 0
    if not phone.startswith('0'):
        phone = '0' + phone
    
    return phone


def validate_slug(slug: str) -> bool:
    """
    Validate URL slug format.
    
    Args:
        slug: URL slug to validate
        
    Returns:
        bool: True if valid
        
    Raises:
        ValidationError: If slug invalid
    """
    if not re.match(r'^[a-z0-9-]+$', slug):
        raise ValidationError(
            'Slug can only contain lowercase letters, numbers, and hyphens.'
        )
    
    if slug.startswith('-') or slug.endswith('-'):
        raise ValidationError(
            'Slug cannot start or end with a hyphen.'
        )
    
    if '--' in slug:
        raise ValidationError(
            'Slug cannot contain consecutive hyphens.'
        )
    
    return True


def sanitize_search_query(query: str, max_length: int = 100) -> str:
    """
    Sanitize search query to prevent injection attacks.
    
    Args:
        query: User search query
        max_length: Maximum query length
        
    Returns:
        str: Sanitized query
    """
    # Truncate to max length
    query = query[:max_length]
    
    # Remove special characters that could be used in SQL injection
    # Keep only alphanumeric, spaces, and basic punctuation
    query = re.sub(r'[^\w\s\-.,&]', '', query)
    
    # Remove SQL keywords (case insensitive)
    sql_keywords = [
        'DROP', 'TABLE', 'DELETE', 'INSERT', 'UPDATE', 'SELECT',
        'UNION', 'WHERE', 'FROM', 'JOIN', 'EXEC', 'EXECUTE'
    ]
    for keyword in sql_keywords:
        query = re.sub(rf'\b{keyword}\b', '', query, flags=re.IGNORECASE)
    
    # Remove excessive whitespace
    query = ' '.join(query.split())
    
    return query


def validate_json_structure(data: dict, required_keys: List[str]) -> bool:
    """
    Validate JSON data structure.
    
    Args:
        data: Dictionary to validate
        required_keys: List of required keys
        
    Returns:
        bool: True if valid
        
    Raises:
        ValidationError: If structure invalid
    """
    missing_keys = [key for key in required_keys if key not in data]
    
    if missing_keys:
        raise ValidationError(
            f'Missing required fields: {", ".join(missing_keys)}'
        )
    
    return True


# Common validators
phone_validator = BangladeshiPhoneValidator()
email_validator = EmailValidator()
