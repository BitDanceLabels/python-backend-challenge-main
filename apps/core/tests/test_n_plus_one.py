import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from apps.core.models import Supplier, Ingredient, PriceListItem

@pytest.mark.django_db
def test_price_items_listing_should_not_n_plus_one():
    supplier = Supplier.objects.create(name="Acme")
    ing = Ingredient.objects.create(name="Tomato")
    # Create 20 items
    for i in range(20):
        PriceListItem.objects.create(
            supplier=supplier, ingredient=ing, sku=f"TOM-{i}", price=1.0, currency="USD",
            pack_size="5 kg", uom="kg", effective_date="2025-01-01"
        )

    # An intentionally naive queryset that would cause N+1 if related fields accessed in a loop.
    qs = PriceListItem.objects.all()  # TODO: select_related('supplier', 'ingredient')

    with CaptureQueriesContext(connection) as ctx:
        # Simulate a view rendering loop that touches related fields
        for obj in qs:
            _ = obj.supplier.name
            _ = obj.ingredient.name if obj.ingredient else None

    # Expectation: queries should be small (<= 3). Naive code will exceed this.
    assert len(ctx.captured_queries) <= 3, (
        "N+1 detected. Use select_related('supplier', 'ingredient') in your queryset."
    )
