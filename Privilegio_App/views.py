from typing import Any

from django.views.generic import TemplateView

from .services import CartPageFlowService, CatalogContextService, ProductDetailFlowService


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


