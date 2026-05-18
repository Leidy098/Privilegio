import logging
from decimal import Decimal

from ..domain.interfaces import PaymentGateway

logger = logging.getLogger(__name__)


class LocalLogPaymentGateway(PaymentGateway):
    def process(self, amount: Decimal, customer_email: str) -> bool:
        logger.info("Payment of %s processed for %s", amount, customer_email)
        return True
