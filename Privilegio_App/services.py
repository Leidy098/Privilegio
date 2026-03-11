from dataclasses import dataclass
from decimal import Decimal
from typing import Any, cast

from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404

from .builders import CartLineInput, ShoppingCartBuilder
from .exceptions import DuplicatedCartItemError, ProductNotAvailableError
from .infra.tax_factory import TaxCalculatorFactory
from .models import CartItem, Product, ShoppingCart


@dataclass(frozen=True)
class CreateCartRequest:
    customer_email: str
    lines: list[CartLineInput]


class CatalogBootstrapService:
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


class CatalogQueryService:
    @staticmethod
    def get_catalog_products() -> list[Product]:
        CatalogBootstrapService.ensure_sample_products()
        return list(Product.objects.filter(is_active=True).order_by("id"))


class CatalogContextService:
    @classmethod
    def build_catalog_context(cls, context: dict[str, Any] | None = None) -> dict[str, Any]:
        resolved_context = dict(context or {})
        products = CatalogQueryService.get_catalog_products()
        resolved_context["products"] = products
        resolved_context["products_json"] = [
            {
                "id": product.pk,
                "name": cast(str, product.name),
                "price": str(cast(Decimal, product.price)),
                "category": cast(str, product.category),
            }
            for product in products
        ]
        return resolved_context


class CartPageFlowService:
    @classmethod
    def build_context(cls, context: dict[str, Any] | None = None) -> dict[str, Any]:
        return CatalogContextService.build_catalog_context(context)


class ProductQueryService:
    @staticmethod
    def get_active_product_or_404(product_id: Any) -> Product:
        if product_id is None:
            raise Http404("Product id is required.")

        return cast(
            Product,
            get_object_or_404(Product, pk=product_id, is_active=True),
        )


class ProductDetailFlowService:
    @staticmethod
    def build_context(product_id: Any, context: dict[str, Any] | None = None) -> dict[str, Any]:
        resolved_context = dict(context or {})
        resolved_context["product"] = ProductQueryService.get_active_product_or_404(product_id)
        return resolved_context


class CartTotalsService:
    def __init__(self, tax_calculator_factory: type[TaxCalculatorFactory] = TaxCalculatorFactory) -> None:
        self.tax_calculator_factory = tax_calculator_factory

    def calculate(self, cart: ShoppingCart) -> tuple[Decimal, Decimal, Decimal]:
        subtotal = self._calculate_subtotal(cart)
        tax = self.tax_calculator_factory.create().calculate(subtotal)
        total = (subtotal + tax).quantize(Decimal("0.01"))
        return subtotal, tax, total

    @staticmethod
    def _calculate_subtotal(cart: ShoppingCart) -> Decimal:
        cart_items = cast(
            list[CartItem],
            list(CartItem.objects.filter(cart=cart)),
        )
        subtotal = sum((cast(Decimal, item.line_total) for item in cart_items), Decimal("0.00"))
        return subtotal.quantize(Decimal("0.01"))


class CartSerializer:
    @staticmethod
    def serialize(cart: ShoppingCart) -> dict[str, Any]:
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


class ShoppingCartService:
    def __init__(
        self,
        totals_service: CartTotalsService | None = None,
    ) -> None:
        self.totals_service = totals_service or CartTotalsService()

    def execute(self, payload: CreateCartRequest) -> dict[str, Any]:
        cart = self.create_cart(payload)
        return CartSerializer.serialize(cart)

    @transaction.atomic
    def create_cart(self, payload: CreateCartRequest) -> ShoppingCart:
        builder = ShoppingCartBuilder(
            customer_email=payload.customer_email,
            lines=payload.lines,
        )
        cart = builder.build()

        subtotal, tax, total = self.totals_service.calculate(cart)

        cart.subtotal = subtotal
        cart.tax = tax
        cart.total = total
        cart.full_clean()
        cart.save(update_fields=["subtotal", "tax", "total", "updated_at"])

        return cart
