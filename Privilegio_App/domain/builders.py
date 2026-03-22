from dataclasses import dataclass
from decimal import Decimal
from typing import cast

from django.core.exceptions import ValidationError
from django.db import transaction

from ..exceptions import DuplicatedCartItemError, ProductNotAvailableError
from ..models import CartItem, Product, ShoppingCart


@dataclass(frozen=True)
class CartLineInput:
    product_id: int
    quantity: int


class ShoppingCartBuilder:
    def __init__(self, customer_email: str, lines: list[CartLineInput]) -> None:
        self.customer_email = customer_email
        self.lines = lines

    def _validate(self) -> None:
        if not self.customer_email:
            raise ValidationError("customer_email is required.")
        if not self.lines:
            raise ValidationError("At least one cart line is required.")

        seen_products: set[int] = set()
        for line in self.lines:
            if line.quantity < 1:
                raise ValidationError("Quantity must be greater than 0.")
            if line.product_id in seen_products:
                raise DuplicatedCartItemError(line.product_id)
            seen_products.add(line.product_id)

    @transaction.atomic
    def build(self) -> ShoppingCart:
        self._validate()

        cart = ShoppingCart(customer_email=self.customer_email)
        cart.full_clean(exclude=["subtotal", "tax", "total"])
        cart.save()

        for line in self.lines:
            product = cast(Product | None, Product.objects.filter(pk=line.product_id, is_active=True).first())
            if not product:
                raise ProductNotAvailableError(line.product_id)

            unit_price = cast(Decimal, product.price)
            line_total = (unit_price * Decimal(line.quantity)).quantize(Decimal("0.01"))

            cart_item = CartItem(
                cart=cart,
                product=product,
                quantity=line.quantity,
                unit_price=unit_price,
                line_total=line_total,
            )
            cart_item.full_clean()
            cart_item.save()

        return cart
