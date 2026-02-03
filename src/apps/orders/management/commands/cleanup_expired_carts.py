"""
Management command to clean up expired guest carts.

This command should be run as a scheduled task (cron job):
    0 3 * * * cd /app && python manage.py cleanup_expired_carts

Deletes guest carts that have expired (expires_at < now).
"""

from django.core.management.base import BaseCommand

from apps.orders.services import CartService


class Command(BaseCommand):
    """Clean up expired guest carts."""

    help = "Delete expired guest carts (30+ days old)"

    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be deleted without actually deleting",
        )

    def handle(self, *args, **options):
        """Execute the command."""
        dry_run = options["dry_run"]

        if dry_run:
            from django.utils import timezone

            from apps.orders.models import Cart

            expired = Cart.objects.filter(
                user__isnull=True, expires_at__lt=timezone.now()
            )
            count = expired.count()

            self.stdout.write(
                self.style.WARNING(f"DRY RUN: Would delete {count} expired carts")
            )

            if count > 0:
                for cart in expired[:10]:  # Show first 10
                    self.stdout.write(
                        f"  - Cart {cart.public_id} "
                        f"(expired: {cart.expires_at}, items: {cart.item_count})"
                    )
                if count > 10:
                    self.stdout.write(f"  ... and {count - 10} more")
        else:
            count = CartService.cleanup_expired_carts()

            if count > 0:
                self.stdout.write(
                    self.style.SUCCESS(f"Deleted {count} expired guest carts")
                )
            else:
                self.stdout.write(self.style.SUCCESS("No expired carts found"))
