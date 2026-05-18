import os
from decimal import Decimal

from ..domain.interfaces import TaxCalculator
from ..domain.logic import ColombiaIVACalculator


class MockTaxCalculator(TaxCalculator):
    def calculate(self, subtotal: Decimal) -> Decimal:
        return Decimal("0.00")


class TaxCalculatorFactory:
    @staticmethod
    def create() -> TaxCalculator:
        provider = os.getenv("TAX_PROVIDER", "REAL").upper()
        if provider == "MOCK":
            return MockTaxCalculator()
        return ColombiaIVACalculator()
