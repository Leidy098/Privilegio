from typing import Any

from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.http import HttpRequest
from django.views.generic import TemplateView
from django.views import View

from .services import (
    CartPageFlowService,
    CatalogContextService,
    ProductDetailFlowService,
    ShoppingCartService,
)


class HomeView(TemplateView):
    template_name = "Privilegio_App/home.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        return CatalogContextService.build_catalog_context(super().get_context_data(**kwargs))


class CartView(TemplateView):
    template_name = "Privilegio_App/cart.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        return CartPageFlowService.build_context(super().get_context_data(**kwargs))


class ProductDetailView(TemplateView):
    template_name = "Privilegio_App/product_detail.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        return ProductDetailFlowService.build_context(
            product_id=self.kwargs.get("pk"),
            context=super().get_context_data(**kwargs),
        )


class ShoppingCartCreateView(View):
    service = ShoppingCartService()

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        try:
            data = self.service.execute(request.body)
        except (ValidationError, KeyError, TypeError, ValueError) as exc:
            return JsonResponse({"error": str(exc)}, status=400)
        return JsonResponse(data, status=201)
