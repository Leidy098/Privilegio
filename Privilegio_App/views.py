from decimal import Decimal
from typing import Any, cast

from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView
from django.views import View

from .models import Product
from .services import ProductCatalogService, ShoppingCartService


class HomeView(TemplateView):
    template_name = "Privilegio_App/home.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        return self._build_catalog_context(super().get_context_data(**kwargs))

    @staticmethod
    def _build_catalog_context(context: dict[str, Any]) -> dict[str, Any]:
        products = ProductCatalogService.get_catalog_products()
        context["products"] = products
        context["products_json"] = [
            {
                "id": product.pk,
                "name": cast(str, product.name),
                "price": str(cast(Decimal, product.price)),
                "category": cast(str, product.category),
            }
            for product in products
        ]
        return context


class CartView(TemplateView):
    template_name = "Privilegio_App/cart.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        return HomeView._build_catalog_context(super().get_context_data(**kwargs))


class ProductDetailView(TemplateView):
    template_name = "Privilegio_App/product_detail.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        product = cast(
            Product,
            get_object_or_404(Product, pk=self.kwargs.get("pk"), is_active=True),
        )
        context["product"] = product
        return context


class ShoppingCartCreateView(View):
    service = ShoppingCartService()

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        try:
            data = self.service.create_cart_from_raw_body(request.body)
        except (ValidationError, KeyError, TypeError, ValueError) as exc:
            return JsonResponse({"error": str(exc)}, status=400)
        return JsonResponse(data, status=201)
