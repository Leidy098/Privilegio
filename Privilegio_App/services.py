import json
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, cast

from django.db import transaction

from .builders import CartLineInput, ShoppingCartBuilder
from .infra.tax_factory import TaxCalculatorFactory
from .models import CartItem, Product, ShoppingCart


@dataclass(frozen=True)
class CreateCartRequest:
    customer_email: str
    lines: list[dict[str, Any]]


class ProductCatalogService:
    SAMPLE_PRODUCTS = (
        {
            "sku": "CAM-URB-001",
            "name": "Camiseta Urban Beige",
            "category": "shirt",
            "description": "Camiseta casual de corte relajado para uso diario.",
            "price": Decimal("79.90"),
        },
        {
            "sku": "PAN-DEN-002",
            "name": "Jean Slim Indigo",
            "category": "pants",
            "description": "Jean slim fit en denim oscuro, facil de combinar.",
            "price": Decimal("129.90"),
        },
        {
            "sku": "JAC-ESS-003",
            "name": "Chaqueta Essential Olive",
            "category": "outerwear",
            "description": "Chaqueta ligera para clima fresco con estilo urbano.",
            "price": Decimal("189.90"),
        },
    )

    @classmethod
    def ensure_sample_products(cls) -> list[Product]:
        products: list[Product] = []
        for item in cls.SAMPLE_PRODUCTS:
            product, _ = Product.objects.get_or_create(
                sku=item["sku"],
                defaults={
                    "name": item["name"],
                    "category": item["category"],
                    "description": item["description"],
                    "price": item["price"],
                    "is_active": True,
                },
            )
            product = cast(Product, product)
            fields_to_update = []
            if not cast(bool, product.is_active):
                product.is_active = True
                fields_to_update.append("is_active")
            if not cast(str, product.description):
                product.description = item["description"]
                fields_to_update.append("description")
            if fields_to_update:
                product.save(update_fields=fields_to_update)
            products.append(product)

        return products

    @classmethod
    def get_catalog_products(cls) -> list[Product]:
        cls.ensure_sample_products()
        return list(Product.objects.filter(is_active=True).order_by("id"))


class ShoppingCartService:
    def create_cart_from_raw_body(self, raw_body: bytes) -> dict:
        body = cast(dict[str, Any], json.loads(raw_body or "{}"))
        payload = CreateCartRequest(
            customer_email=str(body.get("customer_email", "")),
            lines=cast(list[dict[str, Any]], body.get("items", [])),
        )
        cart = self.create_cart(payload)
        return self.serialize_cart(cart)

    @transaction.atomic
    def create_cart(self, payload: CreateCartRequest) -> ShoppingCart:
        normalized_lines = [
            CartLineInput(
                product_id=int(line["product_id"]),
                quantity=int(line["quantity"]),
            )
            for line in payload.lines
        ]

        builder = ShoppingCartBuilder(
            customer_email=payload.customer_email,
            lines=normalized_lines,
        )
        cart = builder.build()

        subtotal = self._calculate_subtotal(cart)
        tax_calculator = TaxCalculatorFactory.create()
        tax = tax_calculator.calculate(subtotal)
        total = (subtotal + tax).quantize(Decimal("0.01"))

        cart.subtotal = subtotal
        cart.tax = tax
        cart.total = total
        cart.full_clean()
        cart.save(update_fields=["subtotal", "tax", "total", "updated_at"])

        return cart

    @staticmethod
    def _calculate_subtotal(cart: ShoppingCart) -> Decimal:
        cart_items = cast(
            list[CartItem],
            list(CartItem.objects.filter(cart=cart)),
        )
        subtotal = sum((cast(Decimal, item.line_total) for item in cart_items), Decimal("0.00"))
        return subtotal.quantize(Decimal("0.01"))

    @staticmethod
    def serialize_cart(cart: ShoppingCart) -> dict:
        cart_items = cast(
            list[CartItem],
            list(CartItem.objects.filter(cart=cart).select_related("product")),
        )
        return {
            "id": cart.pk,
            "customer_email": cast(str, cart.customer_email),
            "status": cast(str, cart.status),
            "subtotal": str(cast(Decimal, cart.subtotal)),
            "tax": str(cast(Decimal, cart.tax)),
            "total": str(cast(Decimal, cart.total)),
            "items": [
                {
                    "product_id": cast(int, cast(Product, item.product).pk),
                    "quantity": cast(int, item.quantity),
                    "unit_price": str(cast(Decimal, item.unit_price)),
                    "line_total": str(cast(Decimal, item.line_total)),
                }
                for item in cart_items
            ],
        }
