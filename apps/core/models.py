from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True

class Supplier(TimestampedModel):
    name = models.CharField(max_length=255)
    country_code = models.CharField(max_length=2, blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [("name", "country_code")]
        ordering = ["name"]

    def __str__(self):
        return self.name

class Ingredient(TimestampedModel):
    name = models.CharField(max_length=255)
    aliases = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                models.functions.Lower('name'),
                name='unique_lower_ingredient_name',
            ),
        ]
        ordering = ["name"]

    def alias_list(self):
        return [a.strip() for a in (self.aliases or "").split(";") if a.strip()]

    def __str__(self):
        return self.name

class PriceListItem(TimestampedModel):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name="price_items")
    ingredient = models.ForeignKey(Ingredient, on_delete=models.SET_NULL, blank=True, null=True, related_name="price_items")
    sku = models.CharField(max_length=255)
    pack_size = models.CharField(max_length=255, blank=True, null=True)
    uom = models.CharField(max_length=64, blank=True, null=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=8, default="USD")
    effective_date = models.DateField()
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="pending")
    source_file = models.CharField(max_length=255, blank=True, null=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="approved_price_items")
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["supplier", "sku", "effective_date"]),
        ]
        ordering = ["-effective_date", "supplier__name", "sku"]

    def __str__(self):
        return f"{self.supplier} {self.sku} {self.effective_date}"
