from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from .infra.tax_factory import TaxCalculatorFactory
from .models import Product, ShoppingCart


class ShoppingCartFlowTests(TestCase):
    def setUp(self):
        self.product_a = Product.objects.create(
            name="Classic White Shirt",
            sku="SHIRT-001",
            category="shirt",
            price=Decimal("59.90"),
            is_active=True,
        )
        self.product_b = Product.objects.create(
            name="Slim Black Pants",
            sku="PANTS-001",
            category="pants",
            price=Decimal("89.90"),
            is_active=True,
        )
        self.url = reverse("cart-create")

    def test_create_cart_success(self):
        payload = {
            "customer_email": "cliente@tienda.com",
            "items": [
                {"product_id": self.product_a.id, "quantity": 1},
                {"product_id": self.product_b.id, "quantity": 2},
            ],
        }

        response = self.client.post(self.url, data=payload, content_type="application/json")

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["customer_email"], "cliente@tienda.com")
        self.assertEqual(data["subtotal"], "239.70")
        self.assertEqual(data["tax"], "45.54")
        self.assertEqual(data["total"], "285.24")
        self.assertEqual(len(data["items"]), 2)
        self.assertEqual(ShoppingCart.objects.count(), 1)

    def test_create_cart_with_invalid_item_returns_400(self):
        payload = {
            "customer_email": "cliente@tienda.com",
            "items": [{"product_id": 9999, "quantity": 1}],
        }

        response = self.client.post(self.url, data=payload, content_type="application/json")

        self.assertEqual(response.status_code, 400)

    @patch.dict("os.environ", {"TAX_PROVIDER": "MOCK"}, clear=False)
    def test_create_cart_uses_mock_tax_provider(self):
        payload = {
            "customer_email": "cliente@tienda.com",
            "items": [{"product_id": self.product_a.id, "quantity": 1}],
        }

        response = self.client.post(self.url, data=payload, content_type="application/json")

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["subtotal"], "59.90")
        self.assertEqual(data["tax"], "0.00")
        self.assertEqual(data["total"], "59.90")


class TaxCalculatorFactoryTests(TestCase):
    @patch.dict("os.environ", {"TAX_PROVIDER": "REAL"}, clear=False)
    def test_factory_returns_real_calculator(self):
        tax = TaxCalculatorFactory.create().calculate(Decimal("100.00"))
        self.assertEqual(tax, Decimal("19.00"))

    @patch.dict("os.environ", {"TAX_PROVIDER": "MOCK"}, clear=False)
    def test_factory_returns_mock_calculator(self):
        tax = TaxCalculatorFactory.create().calculate(Decimal("100.00"))
        self.assertEqual(tax, Decimal("0.00"))
