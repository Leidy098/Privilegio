from abc import ABC, abstractmethod
from decimal import Decimal


class TaxCalculator(ABC):
    @abstractmethod
    def calculate(self, subtotal: Decimal) -> Decimal:
        raise NotImplementedError


class PaymentGateway(ABC):
    @abstractmethod
    def process(self, amount: Decimal, customer_email: str) -> bool:
        raise NotImplementedError
