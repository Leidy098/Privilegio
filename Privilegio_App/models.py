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
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="products/", blank=True, null=True)
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
        return f"Cart #{self.pk} - {self.customer_email}"


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


class CategorySizeChart(models.Model):
    CATEGORY_CHOICES = Product.CATEGORY_CHOICES

    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, unique=True)
    coat_margin = models.DecimalField(max_digits=4, decimal_places=1, default=Decimal("2.0"))

    def __str__(self):
        return f"Tabla de tallas: {self.get_category_display()}"


class SizeEntry(models.Model):
    SIZE_CHOICES = [("S", "S"), ("M", "M"), ("L", "L"), ("XL", "XL")]
    MEASUREMENT_CHOICES = [
        ("chest", "Pecho"),
        ("waist", "Cintura"),
        ("shoulders", "Hombros"),
        ("neck", "Cuello"),
        ("arm_length", "Largo de brazo"),
        ("hips", "Cadera"),
        ("leg_length", "Largo de pierna"),
        ("thigh", "Muslo"),
        ("total_length", "Largo total"),
    ]

    chart = models.ForeignKey(CategorySizeChart, on_delete=models.CASCADE, related_name="entries")
    size = models.CharField(max_length=4, choices=SIZE_CHOICES)
    measurement = models.CharField(max_length=20, choices=MEASUREMENT_CHOICES)
    min_cm = models.DecimalField(max_digits=5, decimal_places=1)
    max_cm = models.DecimalField(max_digits=5, decimal_places=1)

    class Meta:
        unique_together = ("chart", "size", "measurement")
        ordering = ["measurement", "size"]

    def __str__(self):
        return f"{self.chart} | {self.size} | {self.get_measurement_display()}: {self.min_cm}–{self.max_cm} cm"
