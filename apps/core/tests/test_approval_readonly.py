"""
Test that approved PriceListItems have read-only fields enforced.
"""
import pytest
from decimal import Decimal
from datetime import date
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.core.models import Supplier, Ingredient, PriceListItem

User = get_user_model()


@pytest.mark.django_db
class TestApprovalReadOnly:
    """Test the approval workflow and read-only enforcement."""

    @pytest.fixture
    def user(self):
        """Create a test user for approvals."""
        return User.objects.create_user(username='testuser', password='testpass123')

    @pytest.fixture
    def supplier(self):
        """Create a test supplier."""
        return Supplier.objects.create(name='Test Supplier', country_code='US')

    @pytest.fixture
    def ingredient(self):
        """Create a test ingredient."""
        return Ingredient.objects.create(name='Test Ingredient')

    @pytest.fixture
    def price_item(self, supplier, ingredient):
        """Create a test price list item."""
        return PriceListItem.objects.create(
            supplier=supplier,
            ingredient=ingredient,
            sku='TEST-001',
            pack_size='1kg',
            uom='kg',
            price=Decimal('10.50'),
            currency='USD',
            effective_date=date(2025, 1, 1),
            status='pending'
        )

    def test_pending_item_is_editable(self, price_item):
        """Test that pending items can be edited."""
        assert price_item.status == 'pending'

        # Should be able to change price
        original_price = price_item.price
        price_item.price = Decimal('15.00')
        price_item.save()
        price_item.refresh_from_db()

        assert price_item.price == Decimal('15.00')
        assert price_item.price != original_price

    def test_approval_sets_audit_fields(self, price_item, user):
        """Test that approving an item sets the audit fields."""
        assert price_item.approved_by is None
        assert price_item.approved_at is None

        # Approve the item
        price_item.status = 'approved'
        price_item.approved_by = user
        price_item.approved_at = timezone.now()
        price_item.save()

        price_item.refresh_from_db()
        assert price_item.status == 'approved'
        assert price_item.approved_by == user
        assert price_item.approved_at is not None

    def test_unapprove_clears_audit_fields(self, price_item, user):
        """Test that unapproving an item clears the audit fields."""
        # First approve the item
        price_item.status = 'approved'
        price_item.approved_by = user
        price_item.approved_at = timezone.now()
        price_item.save()

        # Now unapprove it
        price_item.status = 'pending'
        price_item.approved_by = None
        price_item.approved_at = None
        price_item.save()

        price_item.refresh_from_db()
        assert price_item.status == 'pending'
        assert price_item.approved_by is None
        assert price_item.approved_at is None

    def test_admin_readonly_logic(self, price_item, user, rf):
        """Test that the admin marks approved items as read-only."""
        from apps.core.admin import PriceListItemAdmin
        from django.contrib.admin.sites import AdminSite

        # Create admin instance
        admin = PriceListItemAdmin(PriceListItem, AdminSite())

        # Create a fake request
        request = rf.get('/')
        request.user = user

        # Test pending item - should have minimal readonly fields
        readonly_fields = admin.get_readonly_fields(request, price_item)
        assert 'price' not in readonly_fields
        assert 'currency' not in readonly_fields

        # Approve the item
        price_item.status = 'approved'
        price_item.approved_by = user
        price_item.approved_at = timezone.now()
        price_item.save()

        # Test approved item - should have price fields as readonly
        readonly_fields = admin.get_readonly_fields(request, price_item)
        assert 'price' in readonly_fields
        assert 'currency' in readonly_fields
        assert 'pack_size' in readonly_fields
        assert 'uom' in readonly_fields
        assert 'effective_date' in readonly_fields
        assert 'ingredient' in readonly_fields

    def test_rejected_item_remains_editable(self, price_item):
        """Test that rejected items remain editable."""
        price_item.status = 'rejected'
        price_item.save()

        # Should still be able to change price
        price_item.price = Decimal('20.00')
        price_item.save()
        price_item.refresh_from_db()

        assert price_item.price == Decimal('20.00')

    def test_multiple_approvals(self, supplier, ingredient, user):
        """Test approving multiple items at once."""
        items = []
        for i in range(3):
            item = PriceListItem.objects.create(
                supplier=supplier,
                ingredient=ingredient,
                sku=f'TEST-{i:03d}',
                price=Decimal('10.00') + Decimal(i),
                currency='USD',
                effective_date=date(2025, 1, i+1),
                status='pending'
            )
            items.append(item)

        # Approve all items
        for item in items:
            item.status = 'approved'
            item.approved_by = user
            item.approved_at = timezone.now()
            item.save()

        # Verify all are approved
        approved_count = PriceListItem.objects.filter(status='approved').count()
        assert approved_count == 3

        # Verify all have audit fields set
        for item in PriceListItem.objects.filter(status='approved'):
            assert item.approved_by == user
            assert item.approved_at is not None


@pytest.fixture
def rf():
    """Request factory fixture."""
    from django.test import RequestFactory
    return RequestFactory()
