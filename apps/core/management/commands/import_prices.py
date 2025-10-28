import csv
import decimal
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from apps.core.models import Supplier, Ingredient, PriceListItem

def normalize_price(val):
    if val is None:
        return None
    s = (val or "").strip().replace("$", "").replace(",", "")
    if not s:
        return None
    return decimal.Decimal(s)

class Command(BaseCommand):
    help = "Import supplier price list from CSV. Idempotent by (supplier, sku, effective_date, price)."

    def add_arguments(self, parser):
        parser.add_argument("--file", required=True, help="Path to CSV file")

    def handle(self, *args, **opts):
        path = Path(opts["file"])
        if not path.exists():
            raise CommandError(f"File not found: {path}")

        created = updated = skipped = 0
        with path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                supplier_name = (row.get("Supplier Name") or row.get("supplier_name") or "").strip()
                sku = (row.get("SKU") or "").strip()
                ingredient_name = (row.get("Item Name") or row.get("item_name") or "").strip()
                pack_size = (row.get("Pack Size") or "").strip()
                uom = (row.get("UOM") or "").strip()
                price = normalize_price(row.get("Price"))
                currency = (row.get("Currency") or "USD").strip()
                effective_date = (row.get("Effective Date") or "").strip()
                aliases = (row.get("Aliases") or "").strip()

                if not supplier_name or not sku or not effective_date:
                    skipped += 1
                    continue
                if price is None:
                    # skip blank price rows
                    skipped += 1
                    continue

                supplier, _ = Supplier.objects.get_or_create(name=supplier_name)
                # try to find ingredient by name or alias (simple contains check)
                ingredient = Ingredient.objects.filter(name__iexact=ingredient_name).first()
                if not ingredient and aliases:
                    # Create/update ingredient with aliases if not exists (optional)
                    ingredient = Ingredient.objects.create(name=ingredient_name, aliases=aliases)

                # idempotent key
                defaults = dict(
                    pack_size=pack_size, uom=uom, price=price, currency=currency,
                    source_file=str(path), ingredient=ingredient
                )
                obj, created_flag = PriceListItem.objects.update_or_create(
                    supplier=supplier, sku=sku, effective_date=effective_date, defaults=defaults
                )
                if created_flag:
                    created += 1
                else:
                    updated += 1

        self.stdout.write(self.style.SUCCESS(
            f"Import complete: created={created}, updated={updated}, skipped={skipped}"
        ))
