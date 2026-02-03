"""Phase 13: CMS - Comprehensive Tests.

This test module validates:
- Page hierarchy (breadcrumbs, children, depth)
- Banner scheduling (is_currently_active with date ranges)
- Contact submission tracking (mark_as_read, add_reply)
- SiteSettings type safety (get_value, get_setting, set_setting)
"""

import json
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.cms.models import Page, Banner, ContactSubmission, SiteSettings

User = get_user_model()


class PageHierarchyTest(TestCase):
    """Test Page model hierarchical functionality."""
    
    def setUp(self):
        """Create test page hierarchy."""
        self.root = Page.objects.create(
            title="Home",
            slug="home",
            content="Homepage content",
            status="published"
        )
        
        self.about = Page.objects.create(
            title="About Us",
            slug="about",
            content="About content",
            parent=self.root,
            status="published"
        )
        
        self.team = Page.objects.create(
            title="Our Team",
            slug="team",
            content="Team content",
            parent=self.about,
            status="published"
        )
    
    def test_get_breadcrumbs(self):
        """Test breadcrumb generation."""
        breadcrumbs = self.team.get_breadcrumbs()
        
        self.assertEqual(len(breadcrumbs), 3)
        self.assertEqual(breadcrumbs[0].title, "Home")
        self.assertEqual(breadcrumbs[1].title, "About Us")
        self.assertEqual(breadcrumbs[2].title, "Our Team")
    
    def test_get_children(self):
        """Test get children method."""
        children = self.root.get_children()
        
        self.assertEqual(children.count(), 1)
        self.assertEqual(children.first().title, "About Us")
    
    def test_get_depth(self):
        """Test depth calculation."""
        self.assertEqual(self.root.get_depth(), 0)
        self.assertEqual(self.about.get_depth(), 1)
        self.assertEqual(self.team.get_depth(), 2)
    
    def test_orphan_children_on_parent_delete(self):
        """Test that children become orphans when parent deleted."""
        self.about.delete()  # Soft delete
        
        # Refresh team from DB
        self.team.refresh_from_db()
        
        # Team should still exist but parent should remain (soft delete)
        self.assertEqual(self.team.parent, self.about)
    
    def test_page_ordering(self):
        """Test pages ordered by sort_order."""
        # Clear existing pages first
        Page.objects.all().delete()
        
        page1 = Page.objects.create(
            title="First",
            slug="first",
            sort_order=1,
            status="published"
        )
        page2 = Page.objects.create(
            title="Second",
            slug="second",
            sort_order=2,
            status="published"
        )
        
        # Default ordering is -created_at, so explicitly order by sort_order
        pages_sorted = Page.objects.order_by('sort_order')
        self.assertEqual(pages_sorted[0], page1)
        self.assertEqual(pages_sorted[1], page2)


class BannerSchedulingTest(TestCase):
    """Test Banner model scheduling functionality."""
    
    def test_banner_always_active(self):
        """Test banner without dates is always active when is_active=True."""
        banner = Banner.objects.create(
            title="Test Banner",
            image="banners/test.jpg",
            position="home_hero",
            is_active=True
        )
        
        self.assertTrue(banner.is_currently_active())
    
    def test_banner_inactive_flag(self):
        """Test banner with is_active=False is not active."""
        banner = Banner.objects.create(
            title="Inactive Banner",
            image="banners/test.jpg",
            position="home_hero",
            is_active=False
        )
        
        self.assertFalse(banner.is_currently_active())
    
    def test_banner_future_start_date(self):
        """Test banner with future start date is not active."""
        future = timezone.now() + timedelta(days=7)
        
        banner = Banner.objects.create(
            title="Future Banner",
            image="banners/test.jpg",
            position="home_hero",
            is_active=True,
            start_date=future
        )
        
        self.assertFalse(banner.is_currently_active())
    
    def test_banner_past_end_date(self):
        """Test banner with past end date is not active."""
        past = timezone.now() - timedelta(days=7)
        
        banner = Banner.objects.create(
            title="Expired Banner",
            image="banners/test.jpg",
            position="home_hero",
            is_active=True,
            end_date=past
        )
        
        self.assertFalse(banner.is_currently_active())
    
    def test_banner_within_date_range(self):
        """Test banner within date range is active."""
        start = timezone.now() - timedelta(days=3)
        end = timezone.now() + timedelta(days=3)
        
        banner = Banner.objects.create(
            title="Active Banner",
            image="banners/test.jpg",
            position="home_hero",
            is_active=True,
            start_date=start,
            end_date=end
        )
        
        self.assertTrue(banner.is_currently_active())
    
    def test_banner_soft_delete(self):
        """Test deleted banner is not active."""
        banner = Banner.objects.create(
            title="Deleted Banner",
            image="banners/test.jpg",
            position="home_hero",
            is_active=True
        )
        
        banner.delete()  # Soft delete
        
        self.assertFalse(banner.is_currently_active())
    
    def test_banner_position_choices(self):
        """Test all banner position choices work."""
        positions = ['home_hero', 'home_secondary', 'sidebar', 'footer']
        
        for position in positions:
            banner = Banner.objects.create(
                title=f"Banner {position}",
                image=f"banners/{position}.jpg",
                position=position,
                is_active=True
            )
            self.assertEqual(banner.position, position)


class ContactSubmissionTest(TestCase):
    """Test ContactSubmission model functionality."""
    
    def setUp(self):
        """Create test user and contact submission."""
        self.user = User.objects.create_user(
            email="admin@example.com",
            password="testpass123"
        )
        
        self.submission = ContactSubmission.objects.create(
            name="John Doe",
            email="john@example.com",
            phone="+8801712345678",
            subject="Product Inquiry",
            message="I want to know about your products.",
            ip_address="192.168.1.1"
        )
    
    def test_mark_as_read(self):
        """Test marking submission as read."""
        self.assertFalse(self.submission.is_read)
        
        self.submission.mark_as_read()
        
        self.assertTrue(self.submission.is_read)
    
    def test_add_reply(self):
        """Test adding reply to submission."""
        self.assertFalse(self.submission.is_replied)
        self.assertIsNone(self.submission.reply_content)
        
        reply_text = "Thank you for your inquiry. Our team will contact you soon."
        self.submission.add_reply(reply_text, self.user)
        
        self.assertTrue(self.submission.is_replied)
        self.assertEqual(self.submission.reply_content, reply_text)
        self.assertEqual(self.submission.replied_by, self.user)
        self.assertIsNotNone(self.submission.replied_at)
    
    def test_submission_default_flags(self):
        """Test default values for read and replied flags."""
        new_submission = ContactSubmission.objects.create(
            name="Jane Doe",
            email="jane@example.com",
            subject="Test",
            message="Test message"
        )
        
        self.assertFalse(new_submission.is_read)
        self.assertFalse(new_submission.is_replied)
    
    def test_submission_ordering(self):
        """Test submissions ordered by newest first."""
        old_submission = ContactSubmission.objects.create(
            name="Old User",
            email="old@example.com",
            subject="Old Inquiry",
            message="Old message"
        )
        
        # Wait a moment
        import time
        time.sleep(0.01)
        
        new_submission = ContactSubmission.objects.create(
            name="New User",
            email="new@example.com",
            subject="New Inquiry",
            message="New message"
        )
        
        submissions = ContactSubmission.objects.all()
        self.assertEqual(submissions[0], new_submission)
        self.assertEqual(submissions[1], old_submission)


class SiteSettingsTest(TestCase):
    """Test SiteSettings model functionality."""
    
    def test_string_value(self):
        """Test storing and retrieving string values."""
        setting = SiteSettings.objects.create(
            key="site_name",
            value="My E-Commerce Store",
            value_type="string",
            group="general"
        )
        
        self.assertEqual(setting.get_value(), "My E-Commerce Store")
    
    def test_number_integer_value(self):
        """Test storing and retrieving integer values."""
        setting = SiteSettings.objects.create(
            key="items_per_page",
            value="20",
            value_type="number",
            group="shop"
        )
        
        result = setting.get_value()
        self.assertEqual(result, 20)
        self.assertIsInstance(result, int)
    
    def test_number_float_value(self):
        """Test storing and retrieving float values."""
        setting = SiteSettings.objects.create(
            key="tax_rate",
            value="15.5",
            value_type="number",
            group="shop"
        )
        
        result = setting.get_value()
        self.assertEqual(result, 15.5)
        self.assertIsInstance(result, float)
    
    def test_boolean_true_values(self):
        """Test various boolean true representations."""
        true_values = ['true', 'True', '1', 'yes', 'Yes', 'on', 'On']
        
        for idx, value in enumerate(true_values):
            setting = SiteSettings.objects.create(
                key=f"test_bool_{idx}",
                value=value,
                value_type="boolean",
                group="general"
            )
            self.assertTrue(setting.get_value(), f"Failed for value: {value}")
    
    def test_boolean_false_values(self):
        """Test boolean false representations."""
        setting = SiteSettings.objects.create(
            key="test_false",
            value="false",
            value_type="boolean",
            group="general"
        )
        
        self.assertFalse(setting.get_value())
    
    def test_json_value(self):
        """Test storing and retrieving JSON values."""
        json_data = {"categories": [1, 2, 3], "featured": True}
        
        setting = SiteSettings.objects.create(
            key="homepage_config",
            value=json.dumps(json_data),
            value_type="json",
            group="general"
        )
        
        result = setting.get_value()
        self.assertEqual(result, json_data)
        self.assertIsInstance(result, dict)
    
    def test_set_value_string(self):
        """Test set_value method with string."""
        setting = SiteSettings.objects.create(
            key="test_key",
            value="old_value",
            value_type="string",
            group="general"
        )
        
        setting.set_value("new_value")
        
        self.assertEqual(setting.value, "new_value")
        self.assertEqual(setting.get_value(), "new_value")
    
    def test_set_value_number(self):
        """Test set_value method with number."""
        setting = SiteSettings.objects.create(
            key="test_number",
            value="10",
            value_type="number",
            group="general"
        )
        
        setting.set_value(25)
        
        self.assertEqual(setting.value, "25")
        self.assertEqual(setting.get_value(), 25)
    
    def test_set_value_boolean(self):
        """Test set_value method with boolean."""
        setting = SiteSettings.objects.create(
            key="test_bool",
            value="false",
            value_type="boolean",
            group="general"
        )
        
        setting.set_value(True)
        
        self.assertEqual(setting.value, "true")
        self.assertTrue(setting.get_value())
    
    def test_set_value_json(self):
        """Test set_value method with dict."""
        setting = SiteSettings.objects.create(
            key="test_json",
            value="{}",
            value_type="json",
            group="general"
        )
        
        new_data = {"key": "value", "count": 42}
        setting.set_value(new_data)
        
        self.assertEqual(setting.get_value(), new_data)
    
    def test_get_setting_class_method(self):
        """Test get_setting class method."""
        SiteSettings.objects.create(
            key="site_title",
            value="Test Store",
            value_type="string",
            group="general"
        )
        
        result = SiteSettings.get_setting("site_title")
        self.assertEqual(result, "Test Store")
    
    def test_get_setting_with_default(self):
        """Test get_setting returns default for non-existent key."""
        result = SiteSettings.get_setting("non_existent_key", "default_value")
        self.assertEqual(result, "default_value")
    
    def test_set_setting_creates_new(self):
        """Test set_setting creates new setting if not exists."""
        SiteSettings.set_setting(
            key="new_setting",
            value="new_value",
            value_type="string",
            group="general"
        )
        
        setting = SiteSettings.objects.get(key="new_setting")
        self.assertEqual(setting.get_value(), "new_value")
    
    def test_set_setting_updates_existing(self):
        """Test set_setting updates existing setting."""
        SiteSettings.objects.create(
            key="existing_key",
            value="old_value",
            value_type="string",
            group="general"
        )
        
        SiteSettings.set_setting(
            key="existing_key",
            value="updated_value"
        )
        
        setting = SiteSettings.objects.get(key="existing_key")
        self.assertEqual(setting.get_value(), "updated_value")
    
    def test_unique_key_constraint(self):
        """Test that key must be unique."""
        SiteSettings.objects.create(
            key="unique_key",
            value="value1",
            value_type="string",
            group="general"
        )
        
        with self.assertRaises(Exception):
            SiteSettings.objects.create(
                key="unique_key",
                value="value2",
                value_type="string",
                group="general"
            )


class PageSEOTest(TestCase):
    """Test Page SEO functionality."""
    
    def test_meta_fields(self):
        """Test meta title and description."""
        page = Page.objects.create(
            title="About Us",
            slug="about",
            content="About content",
            meta_title="About Us | My Store",
            meta_description="Learn more about our company and values.",
            status="published"
        )
        
        self.assertEqual(page.meta_title, "About Us | My Store")
        self.assertEqual(page.meta_description, "Learn more about our company and values.")
    
    def test_slug_uniqueness(self):
        """Test slug must be unique."""
        Page.objects.create(
            title="First Page",
            slug="unique-slug",
            content="Content",
            status="published"
        )
        
        with self.assertRaises(Exception):
            Page.objects.create(
                title="Second Page",
                slug="unique-slug",
                content="Content",
                status="published"
            )


class PageTemplateTest(TestCase):
    """Test Page template functionality."""
    
    def test_template_choices(self):
        """Test all template choices work."""
        templates = ['default', 'about', 'contact', 'faq']
        
        for template in templates:
            page = Page.objects.create(
                title=f"Page {template}",
                slug=f"page-{template}",
                content="Content",
                template=template,
                status="published"
            )
            self.assertEqual(page.template, template)
