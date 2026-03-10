from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.views.generic import TemplateView
from django.views import View

from .services import ProductCatalogService, ShoppingCartService


class HomeView(TemplateView):
    template_name = "Privilegio_App/home.html"

    def get_context_data(self, **kwargs):
        return self._build_catalog_context(super().get_context_data(**kwargs))

    @staticmethod
    def _build_catalog_context(context):
        products = ProductCatalogService.ensure_sample_products()
        context["products"] = products
        context["products_json"] = [
            {
                "id": product.id,
                "name": product.name,
                "price": str(product.price),
                "category": product.category,
            }
            for product in products
        ]
        return context


class CartView(TemplateView):
    template_name = "Privilegio_App/cart.html"

    def get_context_data(self, **kwargs):
        return HomeView._build_catalog_context(super().get_context_data(**kwargs))


class ShoppingCartCreateView(View):
    service = ShoppingCartService()

    def post(self, request, *args, **kwargs):
        try:
            data = self.service.create_cart_from_raw_body(request.body)
        except (ValidationError, KeyError, TypeError, ValueError) as exc:
            return JsonResponse({"error": str(exc)}, status=400)
        return JsonResponse(data, status=201)
