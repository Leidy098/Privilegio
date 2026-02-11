from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


class Product(models.Model):
    CATEGORY_CHOICES = (
        ("shirt", "Shirt"),
        ("pants", "Pants"),
        ("dress", "Dress"),
        ("outerwear", "Outerwear"),
        ("footwear", "Footwear"),
        ("accessory", "Accessory"),
    )

    name = models.CharField(max_length=120)
    sku = models.CharField(max_length=64, unique=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.sku})"


class ShoppingCart(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_CHECKED_OUT = "checked_out"
    STATUS_CHOICES = (
        (STATUS_DRAFT, "Draft"),
        (STATUS_CHECKED_OUT, "Checked out"),
    )

    customer_email = models.EmailField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart #{self.id} - {self.customer_email}"


class CartItem(models.Model):
    cart = models.ForeignKey(ShoppingCart, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name="cart_items", on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    line_total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))

    class Meta:
        unique_together = ("cart", "product")

    def __str__(self):
        return f"{self.product.sku} x {self.quantity}"
