from django.contrib import admin
from django.contrib import messages

from .models import CartItem, Product, ShoppingCart


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "sku", "category", "price", "is_active")
    search_fields = ("name", "sku")
    list_filter = ("category", "is_active")
    fields = ("name", "sku", "category", "description", "image", "price", "is_active")
    actions = ("deactivate_products", "activate_products")

    @admin.action(description="Desactivar productos seleccionados")
    def deactivate_products(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f"{updated} producto(s) desactivado(s). Ya no apareceran en la tienda.",
            level=messages.SUCCESS,
        )

    @admin.action(description="Activar productos seleccionados")
    def activate_products(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            f"{updated} producto(s) activado(s).",
            level=messages.SUCCESS,
        )


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ("id", "customer_email", "status", "subtotal", "tax", "total", "created_at")
    search_fields = ("customer_email",)
    list_filter = ("status", "created_at")
    inlines = [CartItemInline]
