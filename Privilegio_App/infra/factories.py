import os
from decimal import Decimal


class TaxCalculator:
    def calculate(self, subtotal: Decimal) -> Decimal:
        raise NotImplementedError


class ColombiaRealTaxCalculator(TaxCalculator):
    def calculate(self, subtotal: Decimal) -> Decimal:
        return (subtotal * Decimal("0.19")).quantize(Decimal("0.01"))


class MockTaxCalculator(TaxCalculator):
    def calculate(self, subtotal: Decimal) -> Decimal:
        return Decimal("0.00")


class TaxCalculatorFactory:
    @staticmethod
    def create() -> TaxCalculator:
        provider = os.getenv("TAX_PROVIDER", "REAL").upper()
        if provider == "MOCK":
            return MockTaxCalculator()
        return ColombiaRealTaxCalculator()
