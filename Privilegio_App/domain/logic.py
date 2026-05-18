from decimal import Decimal

from .interfaces import TaxCalculator


class ColombiaIVACalculator(TaxCalculator):
    def calculate(self, subtotal: Decimal) -> Decimal:
        return (subtotal * Decimal("0.19")).quantize(Decimal("0.01"))
