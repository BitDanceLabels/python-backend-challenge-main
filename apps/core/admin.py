from django.contrib import admin
from django.utils import timezone
from django.contrib import messages
from django.http import HttpResponse
import csv
from .models import Supplier, Ingredient, PriceListItem

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    list_display = ("name", "country_code", "is_active")
    list_filter = ("is_active", "country_code")

@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    search_fields = ("name", "aliases")
    list_display = ("name", "is_active")

@admin.register(PriceListItem)
class PriceListItemAdmin(admin.ModelAdmin):
    list_display = ("supplier", "sku", "ingredient", "price", "currency", "effective_date", "status")
    list_filter = ("supplier", "status", "currency")
    search_fields = ("sku", "supplier__name", "ingredient__name", "ingredient__aliases")
    actions = ["approve_items", "reject_items", "unapprove_items", "export_to_csv"]

    readonly_fields_when_approved = ("price", "currency", "pack_size", "uom", "effective_date", "source_file", "ingredient")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('supplier', 'ingredient', 'approved_by')

    def get_readonly_fields(self, request, obj=None):
        ro = list(super().get_readonly_fields(request, obj))
        if obj and obj.status == "approved":
            ro = list(set(ro) | set(self.readonly_fields_when_approved))
        return ro

    def approve_items(self, request, queryset):
        updated = 0
        for item in queryset:
            item.status = "approved"
            item.approved_by = request.user
            item.approved_at = timezone.now()
            item.save(update_fields=["status", "approved_by", "approved_at"])
            updated += 1
        self.message_user(request, f"Approved {updated} items.", level=messages.SUCCESS)
    approve_items.short_description = "Approve selected items"

    def reject_items(self, request, queryset):
        updated = queryset.update(status="rejected")
        self.message_user(request, f"Rejected {updated} items.", level=messages.WARNING)
    reject_items.short_description = "Reject selected items"

    def unapprove_items(self, request, queryset):
        updated = 0
        for item in queryset:
            if item.status == "approved":
                item.status = "pending"
                item.approved_by = None
                item.approved_at = None
                item.save(update_fields=["status", "approved_by", "approved_at"])
                updated += 1
        self.message_user(request, f"Unapproved {updated} items.", level=messages.INFO)
    unapprove_items.short_description = "Unapprove selected items"

    def export_to_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="price_list_items.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'Supplier Name',
            'SKU',
            'Ingredient Name',
            'Pack Size',
            'UOM',
            'Price',
            'Currency',
            'Effective Date',
            'Status',
            'Source File',
            'Approved By',
            'Approved At'
        ])

        for item in queryset.select_related('supplier', 'ingredient', 'approved_by'):
            writer.writerow([
                item.supplier.name,
                item.sku,
                item.ingredient.name if item.ingredient else '',
                item.pack_size or '',
                item.uom or '',
                item.price if item.price else '',
                item.currency,
                item.effective_date.strftime('%Y-%m-%d'),
                item.status,
                item.source_file or '',
                item.approved_by.username if item.approved_by else '',
                item.approved_at.strftime('%Y-%m-%d %H:%M:%S') if item.approved_at else ''
            ])

        return response
    export_to_csv.short_description = "Export selected items to CSV"
