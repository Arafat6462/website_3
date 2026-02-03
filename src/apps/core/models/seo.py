"""
SEO Model.

This module provides an abstract model for SEO (Search Engine Optimization)
fields including slug, meta title, and meta description.

Use for any content that needs SEO optimization and URL slugs.
"""

from typing import Any

from django.db import models

from apps.core.models.base import TimeStampedModel


class SEOModel(TimeStampedModel):
    """
    Abstract model providing SEO fields.

    Adds slug for URLs and meta fields for search engine optimization.
    The slug field is unique and indexed for efficient lookups.

    Attributes:
        slug: URL-friendly identifier, must be unique.
        meta_title: Page title for search engines (max 60 chars recommended).
        meta_description: Page description for search results (max 160 chars).

    Auto-Slug Generation:
        Override get_slug_source() to return the field used for auto-generating
        slugs. Default is 'name', but can be 'title' or any string field.

    Example:
        class Product(SEOModel):
            name = models.CharField(max_length=255)

            def get_slug_source(self) -> str:
                return self.name

        # Slug auto-generated from name
        product = Product(name="Cotton T-Shirt")
        product.save()  # slug = "cotton-t-shirt"
    """

    slug = models.SlugField(
        verbose_name="URL Slug",
        max_length=255,
        unique=True,
        db_index=True,
        help_text="URL-friendly version of the name. Auto-generated if left blank.",
    )

    meta_title = models.CharField(
        verbose_name="Meta Title",
        max_length=70,
        blank=True,
        help_text="SEO title for search engines. Recommended: 50-60 characters.",
    )

    meta_description = models.TextField(
        verbose_name="Meta Description",
        max_length=160,
        blank=True,
        help_text="SEO description for search results. Recommended: 150-160 characters.",
    )

    class Meta:
        abstract = True

    def get_slug_source(self) -> str:
        """
        Return the value to use for slug generation.

        Override this method in child classes to specify which field
        should be used to generate the slug.

        Returns:
            String value to slugify.

        Example:
            def get_slug_source(self) -> str:
                return self.title  # For Page model
        """
        # Default: try 'name' field, fall back to empty string
        return getattr(self, "name", "") or getattr(self, "title", "") or ""

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Save the model, auto-generating slug if empty.

        If slug is not provided, generates one from get_slug_source().
        Uses the generate_unique_slug utility to ensure uniqueness.

        Args:
            *args: Positional arguments passed to parent save().
            **kwargs: Keyword arguments passed to parent save().
        """
        # Auto-generate slug if not provided
        if not self.slug:
            from apps.core.utils import generate_unique_slug

            source = self.get_slug_source()
            if source:
                self.slug = generate_unique_slug(
                    model_class=self.__class__,
                    value=source,
                    slug_field="slug",
                    instance=self,
                )

        super().save(*args, **kwargs)

    def get_meta_title(self) -> str:
        """
        Get the effective meta title.

        Returns meta_title if set, otherwise falls back to
        name/title field.

        Returns:
            String to use as page title.
        """
        if self.meta_title:
            return self.meta_title

        return self.get_slug_source()

    def get_meta_description(self) -> str:
        """
        Get the effective meta description.

        Returns meta_description if set. Child classes can override
        to provide automatic description from content.

        Returns:
            String to use as meta description.
        """
        return self.meta_description or ""

    @property
    def seo_data(self) -> dict[str, str]:
        """
        Get all SEO data as a dictionary.

        Useful for passing to templates or API responses.

        Returns:
            Dictionary with title, description, and slug.
        """
        return {
            "title": self.get_meta_title(),
            "description": self.get_meta_description(),
            "slug": self.slug,
        }
