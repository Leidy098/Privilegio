from django.contrib import admin

from .models import CartItem, Product, ShoppingCart


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "sku", "category", "price", "is_active")
    search_fields = ("name", "sku")
    list_filter = ("category", "is_active")


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ("id", "customer_email", "status", "subtotal", "tax", "total", "created_at")
    search_fields = ("customer_email",)
    list_filter = ("status", "created_at")
    inlines = [CartItemInline]
