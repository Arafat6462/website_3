"""CMS models for content management.

This module contains models for managing website content including:
- Pages (hierarchical structure)
- Banners (scheduled promotional content)
- Contact form submissions
- Site-wide settings (key-value configuration)
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import URLValidator
from apps.core.models import TimeStampedModel, SoftDeleteModel

User = get_user_model()


class Page(SoftDeleteModel):
    """Page model for CMS content.
    
    Supports hierarchical page structure with parent-child relationships.
    Each page has a title, slug, content, and optional parent for nesting.
    
    Attributes:
        title (str): Page title (max 200 chars)
        slug (str): URL-friendly slug (unique)
        content (text): Page content (rich text)
        template (str): Template type to use
        parent (Page): Parent page for hierarchy (optional)
        status (str): Publication status (draft/published)
        sort_order (int): Display order within same parent
        meta_title (str): SEO meta title (optional)
        meta_description (str): SEO meta description (optional)
        is_deleted (bool): Soft delete flag
        created_at (datetime): Creation timestamp
        updated_at (datetime): Last update timestamp
    """
    
    TEMPLATE_CHOICES = [
        ('default', 'Default'),
        ('about', 'About Us'),
        ('contact', 'Contact'),
        ('faq', 'FAQ'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
    ]
    
    title = models.CharField(
        max_length=200,
        help_text="Page title displayed in navigation and header"
    )
    
    slug = models.SlugField(
        max_length=200,
        unique=True,
        help_text="URL-friendly version of title (auto-generated)"
    )
    
    content = models.TextField(
        blank=True,
        help_text="Page content (supports rich text/HTML)"
    )
    
    template = models.CharField(
        max_length=50,
        choices=TEMPLATE_CHOICES,
        default='default',
        help_text="Template to use for rendering this page"
    )
    
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        help_text="Parent page for hierarchical structure"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        db_index=True,
        help_text="Publication status"
    )
    
    sort_order = models.PositiveIntegerField(
        default=0,
        help_text="Display order (lower numbers appear first)"
    )
    
    # SEO fields
    meta_title = models.CharField(
        max_length=200,
        blank=True,
        help_text="SEO meta title (defaults to page title)"
    )
    
    meta_description = models.TextField(
        max_length=300,
        blank=True,
        help_text="SEO meta description"
    )
    
    class Meta:
        """Meta options for Page model."""
        
        verbose_name = "Page"
        verbose_name_plural = "Pages"
        ordering = ['sort_order', 'title']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['status', 'is_deleted']),
            models.Index(fields=['parent', 'sort_order']),
        ]
    
    def __str__(self):
        """String representation of page."""
        return self.title
    
    def get_breadcrumbs(self):
        """Get breadcrumb trail from root to this page.
        
        Returns:
            list: List of Page objects from root to current page
        """
        breadcrumbs = [self]
        current = self.parent
        
        while current:
            breadcrumbs.insert(0, current)
            current = current.parent
        
        return breadcrumbs
    
    def get_children(self):
        """Get immediate child pages.
        
        Returns:
            QuerySet: Published child pages ordered by sort_order
        """
        return self.children.filter(
            status='published',
            is_deleted=False
        ).order_by('sort_order')
    
    def get_depth(self):
        """Calculate depth level in hierarchy.
        
        Returns:
            int: Depth level (0 for root pages)
        """
        depth = 0
        current = self.parent
        
        while current:
            depth += 1
            current = current.parent
        
        return depth


class Banner(SoftDeleteModel):
    """Banner model for promotional content.
    
    Supports scheduled display with start/end dates and positioning.
    Used for hero images, promotions, and announcements.
    
    Attributes:
        title (str): Banner title (admin reference)
        image (ImageField): Banner image
        link_url (str): Click-through URL (optional)
        position (str): Display position on site
        is_active (bool): Active status
        start_date (datetime): Display start date (optional)
        end_date (datetime): Display end date (optional)
        sort_order (int): Display order within same position
        is_deleted (bool): Soft delete flag
        created_at (datetime): Creation timestamp
        updated_at (datetime): Last update timestamp
    """
    
    POSITION_CHOICES = [
        ('home_hero', 'Homepage Hero'),
        ('home_secondary', 'Homepage Secondary'),
        ('sidebar', 'Sidebar'),
        ('footer', 'Footer'),
    ]
    
    title = models.CharField(
        max_length=200,
        help_text="Banner title (for admin reference only)"
    )
    
    image = models.ImageField(
        upload_to='banners/',
        help_text="Banner image (recommended: 1920x600 for hero)"
    )
    
    link_url = models.CharField(
        max_length=500,
        blank=True,
        validators=[URLValidator()],
        help_text="Click destination URL (optional)"
    )
    
    position = models.CharField(
        max_length=50,
        choices=POSITION_CHOICES,
        default='home_hero',
        db_index=True,
        help_text="Where to display this banner"
    )
    
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Active banners are eligible for display"
    )
    
    start_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Start displaying from this date/time (optional)"
    )
    
    end_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Stop displaying after this date/time (optional)"
    )
    
    sort_order = models.PositiveIntegerField(
        default=0,
        help_text="Display order (lower numbers appear first)"
    )
    
    class Meta:
        """Meta options for Banner model."""
        
        verbose_name = "Banner"
        verbose_name_plural = "Banners"
        ordering = ['position', 'sort_order']
        indexes = [
            models.Index(fields=['position', 'is_active', 'sort_order']),
            models.Index(fields=['is_active', 'start_date', 'end_date']),
        ]
    
    def __str__(self):
        """String representation of banner."""
        return f"{self.title} ({self.get_position_display()})"
    
    def is_currently_active(self):
        """Check if banner should be displayed now.
        
        Checks is_active flag and date range constraints.
        
        Returns:
            bool: True if banner should be displayed
        """
        from django.utils import timezone
        
        if not self.is_active or self.is_deleted:
            return False
        
        now = timezone.now()
        
        # Check start date
        if self.start_date and now < self.start_date:
            return False
        
        # Check end date
        if self.end_date and now > self.end_date:
            return False
        
        return True


class ContactSubmission(TimeStampedModel):
    """Contact form submission model.
    
    Stores customer inquiries submitted through contact form.
    Supports admin replies and read/unread tracking.
    
    Attributes:
        name (str): Submitter name
        email (str): Submitter email
        phone (str): Submitter phone (optional)
        subject (str): Message subject
        message (text): Message content
        is_read (bool): Read status
        is_replied (bool): Reply status
        reply_content (text): Admin reply (optional)
        replied_by (User): Staff who replied (optional)
        replied_at (datetime): Reply timestamp (optional)
        ip_address (str): Submitter IP address (optional)
        created_at (datetime): Submission timestamp
    """
    
    name = models.CharField(
        max_length=200,
        help_text="Full name of person contacting"
    )
    
    email = models.EmailField(
        help_text="Email address for reply"
    )
    
    phone = models.CharField(
        max_length=20,
        blank=True,
        help_text="Phone number (optional)"
    )
    
    subject = models.CharField(
        max_length=300,
        help_text="Subject of inquiry"
    )
    
    message = models.TextField(
        help_text="Message content"
    )
    
    is_read = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether admin has read this message"
    )
    
    is_replied = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether admin has replied to this message"
    )
    
    reply_content = models.TextField(
        null=True,
        blank=True,
        help_text="Admin's reply to the inquiry"
    )
    
    replied_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contact_replies',
        help_text="Staff member who replied"
    )
    
    replied_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When reply was sent"
    )
    
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of submitter"
    )
    
    class Meta:
        """Meta options for ContactSubmission model."""
        
        verbose_name = "Contact Submission"
        verbose_name_plural = "Contact Submissions"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['is_read', '-created_at']),
            models.Index(fields=['is_replied', '-created_at']),
        ]
    
    def __str__(self):
        """String representation of contact submission."""
        return f"{self.name} - {self.subject}"
    
    def mark_as_read(self):
        """Mark submission as read."""
        self.is_read = True
        self.save(update_fields=['is_read'])
    
    def add_reply(self, content, replied_by):
        """Add admin reply to submission.
        
        Args:
            content (str): Reply message content
            replied_by (User): Staff user sending reply
        """
        from django.utils import timezone
        
        self.reply_content = content
        self.replied_by = replied_by
        self.replied_at = timezone.now()
        self.is_replied = True
        self.is_read = True  # Auto-mark as read when replying
        self.save(update_fields=[
            'reply_content',
            'replied_by',
            'replied_at',
            'is_replied',
            'is_read'
        ])


class SiteSettings(models.Model):
    """Site-wide settings stored as key-value pairs.
    
    Flexible configuration system for site-wide settings.
    Supports different value types (string, number, boolean, JSON).
    
    Attributes:
        key (str): Setting identifier (unique)
        value (text): Setting value (type depends on value_type)
        value_type (str): Type of value stored
        group (str): Settings group for organization
        description (str): Human-readable description
    
    Examples:
        - site_name: "My E-Commerce Store"
        - items_per_page: "20"
        - enable_reviews: "true"
        - social_links: {"facebook": "...", "twitter": "..."}
    """
    
    VALUE_TYPE_CHOICES = [
        ('string', 'String'),
        ('number', 'Number'),
        ('boolean', 'Boolean'),
        ('json', 'JSON'),
    ]
    
    GROUP_CHOICES = [
        ('general', 'General'),
        ('shop', 'Shop'),
        ('seo', 'SEO'),
        ('social', 'Social Media'),
        ('email', 'Email'),
        ('advanced', 'Advanced'),
    ]
    
    key = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="Unique setting identifier (e.g., 'site_name')"
    )
    
    value = models.TextField(
        blank=True,
        help_text="Setting value (format depends on value_type)"
    )
    
    value_type = models.CharField(
        max_length=20,
        choices=VALUE_TYPE_CHOICES,
        default='string',
        help_text="Type of value stored"
    )
    
    group = models.CharField(
        max_length=50,
        choices=GROUP_CHOICES,
        default='general',
        db_index=True,
        help_text="Settings group for organization"
    )
    
    description = models.CharField(
        max_length=300,
        blank=True,
        help_text="Human-readable description of this setting"
    )
    
    class Meta:
        """Meta options for SiteSettings model."""
        
        verbose_name = "Site Setting"
        verbose_name_plural = "Site Settings"
        ordering = ['group', 'key']
        indexes = [
            models.Index(fields=['key']),
            models.Index(fields=['group']),
        ]
    
    def __str__(self):
        """String representation of setting."""
        return f"{self.key} = {self.value[:50]}"
    
    def get_value(self):
        """Get typed value based on value_type.
        
        Returns:
            Typed value (str, int, float, bool, or dict)
        """
        import json
        
        if self.value_type == 'number':
            try:
                # Try int first
                if '.' not in self.value:
                    return int(self.value)
                # Fall back to float
                return float(self.value)
            except (ValueError, TypeError):
                return 0
        
        elif self.value_type == 'boolean':
            return self.value.lower() in ('true', '1', 'yes', 'on')
        
        elif self.value_type == 'json':
            try:
                return json.loads(self.value)
            except (json.JSONDecodeError, TypeError):
                return {}
        
        # Default: return as string
        return self.value
    
    def set_value(self, new_value):
        """Set value with automatic type conversion.
        
        Args:
            new_value: Value to set (will be converted to string)
        """
        import json
        
        if self.value_type == 'json':
            if isinstance(new_value, (dict, list)):
                self.value = json.dumps(new_value)
            else:
                self.value = str(new_value)
        elif self.value_type == 'boolean':
            # Convert boolean to lowercase string
            self.value = 'true' if new_value else 'false'
        else:
            self.value = str(new_value)
        
        self.save(update_fields=['value'])
    
    @classmethod
    def get_setting(cls, key, default=None):
        """Get setting value by key.
        
        Args:
            key (str): Setting key
            default: Default value if setting doesn't exist
        
        Returns:
            Typed setting value or default
        """
        try:
            setting = cls.objects.get(key=key)
            return setting.get_value()
        except cls.DoesNotExist:
            return default
    
    @classmethod
    def set_setting(cls, key, value, value_type='string', group='general', description=''):
        """Set or update setting value.
        
        Args:
            key (str): Setting key
            value: Value to set
            value_type (str): Type of value
            group (str): Settings group
            description (str): Setting description
        
        Returns:
            SiteSettings: Created or updated setting instance
        """
        setting, created = cls.objects.get_or_create(
            key=key,
            defaults={
                'value_type': value_type,
                'group': group,
                'description': description,
            }
        )
        
        if not created:
            # Update existing setting
            setting.value_type = value_type
            setting.group = group
            if description:
                setting.description = description
        
        setting.set_value(value)
        return setting
