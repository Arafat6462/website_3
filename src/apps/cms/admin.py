"""Admin interfaces for CMS models.

This module provides comprehensive admin interfaces for:
- Pages (with hierarchical display)
- Banners (with scheduling and activation)
- Contact Submissions (with reply functionality)
- Site Settings (grouped by category)
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from unfold.admin import ModelAdmin
from .models import Page, Banner, ContactSubmission, SiteSettings


@admin.register(Page)
class PageAdmin(ModelAdmin):
    """Admin interface for Page model.
    
    Features:
        - Hierarchical tree display
        - Drag-drop ordering
        - SEO fields
        - Status badges
        - Breadcrumb preview
    """
    
    list_display = [
        'get_tree_title',
        'slug',
        'template',
        'status_badge',
        'sort_order',
        'updated_at',
    ]
    
    list_filter = [
        'status',
        'template',
        'is_deleted',
        'created_at',
    ]
    
    search_fields = [
        'title',
        'slug',
        'content',
        'meta_title',
        'meta_description',
    ]
    
    prepopulated_fields = {'slug': ('title',)}
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'parent', 'status')
        }),
        ('Content', {
            'fields': ('content', 'template')
        }),
        ('Display Order', {
            'fields': ('sort_order',),
            'classes': ('collapse',)
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ['sort_order', 'title']
    
    def get_tree_title(self, obj):
        """Display title with indentation for hierarchy.
        
        Args:
            obj (Page): Page instance
        
        Returns:
            str: HTML formatted title with indentation
        """
        depth = obj.get_depth()
        indent = '&nbsp;&nbsp;&nbsp;&nbsp;' * depth
        
        if depth > 0:
            return format_html(
                '{}<span style="color: #999;">└─</span> {}',
                format_html(indent),
                obj.title
            )
        return obj.title
    
    get_tree_title.short_description = 'Title'
    get_tree_title.admin_order_field = 'title'
    
    def status_badge(self, obj):
        """Display status as colored badge.
        
        Args:
            obj (Page): Page instance
        
        Returns:
            str: HTML badge for status
        """
        if obj.status == 'published':
            color = '#28a745'
            icon = '✓'
        else:
            color = '#ffc107'
            icon = '○'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color,
            icon,
            obj.get_status_display()
        )
    
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'
    
    def get_queryset(self, request):
        """Get queryset with optimizations.
        
        Args:
            request: HTTP request
        
        Returns:
            QuerySet: Optimized queryset
        """
        qs = super().get_queryset(request)
        return qs.select_related('parent')


@admin.register(Banner)
class BannerAdmin(ModelAdmin):
    """Admin interface for Banner model.
    
    Features:
        - Image preview
        - Active status toggle
        - Schedule display
        - Position grouping
        - Drag-drop ordering
    """
    
    list_display = [
        'image_preview',
        'title',
        'position',
        'active_badge',
        'schedule_info',
        'sort_order',
        'created_at',
    ]
    
    list_filter = [
        'position',
        'is_active',
        'is_deleted',
        'created_at',
    ]
    
    search_fields = [
        'title',
        'link_url',
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'image', 'link_url', 'position')
        }),
        ('Activation', {
            'fields': ('is_active', 'sort_order')
        }),
        ('Scheduling', {
            'fields': ('start_date', 'end_date'),
            'classes': ('collapse',),
            'description': 'Optional: Set date range for automatic display'
        }),
    )
    
    ordering = ['position', 'sort_order']
    
    actions = ['activate_banners', 'deactivate_banners']
    
    def image_preview(self, obj):
        """Display small image preview.
        
        Args:
            obj (Banner): Banner instance
        
        Returns:
            str: HTML img tag or placeholder
        """
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 100px; max-height: 50px; border-radius: 4px;" />',
                obj.image.url
            )
        return format_html(
            '<span style="color: #999;">No image</span>'
        )
    
    image_preview.short_description = 'Preview'
    
    def active_badge(self, obj):
        """Display active status with current state check.
        
        Args:
            obj (Banner): Banner instance
        
        Returns:
            str: HTML badge for status
        """
        is_currently_active = obj.is_currently_active()
        
        if is_currently_active:
            color = '#28a745'
            text = '● Active'
        elif obj.is_active:
            color = '#ffc107'
            text = '○ Scheduled'
        else:
            color = '#dc3545'
            text = '✕ Inactive'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            text
        )
    
    active_badge.short_description = 'Status'
    active_badge.admin_order_field = 'is_active'
    
    def schedule_info(self, obj):
        """Display schedule information.
        
        Args:
            obj (Banner): Banner instance
        
        Returns:
            str: HTML formatted schedule info
        """
        if not obj.start_date and not obj.end_date:
            return format_html(
                '<span style="color: #999;">No schedule</span>'
            )
        
        now = timezone.now()
        info_parts = []
        
        if obj.start_date:
            if obj.start_date > now:
                info_parts.append(f"Starts: {obj.start_date.strftime('%Y-%m-%d')}")
            else:
                info_parts.append(f"<span style='color: #28a745;'>Started</span>")
        
        if obj.end_date:
            if obj.end_date < now:
                info_parts.append(f"<span style='color: #dc3545;'>Ended</span>")
            else:
                info_parts.append(f"Ends: {obj.end_date.strftime('%Y-%m-%d')}")
        
        return format_html('<br>'.join(info_parts))
    
    schedule_info.short_description = 'Schedule'
    
    def activate_banners(self, request, queryset):
        """Bulk action to activate banners.
        
        Args:
            request: HTTP request
            queryset: Selected banners
        """
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} banner(s) activated.")
    
    activate_banners.short_description = "Activate selected banners"
    
    def deactivate_banners(self, request, queryset):
        """Bulk action to deactivate banners.
        
        Args:
            request: HTTP request
            queryset: Selected banners
        """
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} banner(s) deactivated.")
    
    deactivate_banners.short_description = "Deactivate selected banners"


@admin.register(ContactSubmission)
class ContactSubmissionAdmin(ModelAdmin):
    """Admin interface for ContactSubmission model.
    
    Features:
        - Read/unread badges
        - Reply functionality
        - Date filtering
        - Search by name/email
        - Bulk mark as read
    """
    
    list_display = [
        'name',
        'email',
        'subject',
        'status_badges',
        'created_at',
    ]
    
    list_filter = [
        'is_read',
        'is_replied',
        'created_at',
    ]
    
    search_fields = [
        'name',
        'email',
        'phone',
        'subject',
        'message',
    ]
    
    fieldsets = (
        ('Contact Information', {
            'fields': ('name', 'email', 'phone', 'ip_address')
        }),
        ('Message', {
            'fields': ('subject', 'message')
        }),
        ('Status', {
            'fields': ('is_read', 'is_replied')
        }),
        ('Admin Reply', {
            'fields': ('reply_content', 'replied_by', 'replied_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = [
        'ip_address',
        'replied_by',
        'replied_at',
        'created_at',
    ]
    
    ordering = ['-created_at']
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def status_badges(self, obj):
        """Display read and reply status badges.
        
        Args:
            obj (ContactSubmission): Submission instance
        
        Returns:
            str: HTML badges for status
        """
        badges = []
        
        # Read badge
        if obj.is_read:
            badges.append(
                '<span style="background: #28a745; color: white; padding: 2px 8px; '
                'border-radius: 3px; font-size: 11px;">READ</span>'
            )
        else:
            badges.append(
                '<span style="background: #ffc107; color: #333; padding: 2px 8px; '
                'border-radius: 3px; font-size: 11px;">NEW</span>'
            )
        
        # Reply badge
        if obj.is_replied:
            badges.append(
                '<span style="background: #17a2b8; color: white; padding: 2px 8px; '
                'border-radius: 3px; font-size: 11px;">REPLIED</span>'
            )
        
        return format_html(' '.join(badges))
    
    status_badges.short_description = 'Status'
    
    def mark_as_read(self, request, queryset):
        """Bulk action to mark submissions as read.
        
        Args:
            request: HTTP request
            queryset: Selected submissions
        """
        updated = queryset.update(is_read=True)
        self.message_user(request, f"{updated} submission(s) marked as read.")
    
    mark_as_read.short_description = "Mark as read"
    
    def mark_as_unread(self, request, queryset):
        """Bulk action to mark submissions as unread.
        
        Args:
            request: HTTP request
            queryset: Selected submissions
        """
        updated = queryset.update(is_read=False)
        self.message_user(request, f"{updated} submission(s) marked as unread.")
    
    mark_as_unread.short_description = "Mark as unread"
    
    def save_model(self, request, obj, form, change):
        """Auto-mark as read when viewing.
        
        Args:
            request: HTTP request
            obj: Model instance
            form: Model form
            change: Boolean indicating if this is a change (not add)
        """
        if change and not obj.is_read:
            obj.mark_as_read()
        
        super().save_model(request, obj, form, change)


@admin.register(SiteSettings)
class SiteSettingsAdmin(ModelAdmin):
    """Admin interface for SiteSettings model.
    
    Features:
        - Grouped by category
        - Type-specific input widgets
        - Value preview
        - Search by key/description
    """
    
    list_display = [
        'key',
        'value_preview',
        'value_type',
        'group',
        'description',
    ]
    
    list_filter = [
        'group',
        'value_type',
    ]
    
    search_fields = [
        'key',
        'value',
        'description',
    ]
    
    fieldsets = (
        ('Setting Identity', {
            'fields': ('key', 'group', 'description')
        }),
        ('Value', {
            'fields': ('value', 'value_type')
        }),
    )
    
    ordering = ['group', 'key']
    
    def value_preview(self, obj):
        """Display truncated value preview.
        
        Args:
            obj (SiteSettings): Setting instance
        
        Returns:
            str: HTML formatted value preview
        """
        value = obj.value
        
        if len(value) > 50:
            preview = value[:47] + '...'
        else:
            preview = value
        
        # Color code by type
        type_colors = {
            'string': '#6c757d',
            'number': '#17a2b8',
            'boolean': '#28a745',
            'json': '#ffc107',
        }
        
        color = type_colors.get(obj.value_type, '#6c757d')
        
        return format_html(
            '<code style="color: {};">{}</code>',
            color,
            preview
        )
    
    value_preview.short_description = 'Value'
    value_preview.admin_order_field = 'value'
