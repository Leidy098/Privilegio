from typing import Any, cast

from django.core.exceptions import ValidationError
from django.http import HttpRequest
from django.views.generic import TemplateView
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .builders import CartLineInput
from .exceptions import DuplicatedCartItemError, ProductNotAvailableError
from .serializers import CartOutputSerializer, CreateCartInputSerializer
from .services import (
    CartPageFlowService,
    CatalogContextService,
    CreateCartRequest,
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


class ShoppingCartCreateView(APIView):
    service = ShoppingCartService()

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        input_serializer = CreateCartInputSerializer(data=request.data)
        if not input_serializer.is_valid():
            return Response(input_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = cast(dict[str, Any], input_serializer.validated_data)
        payload = CreateCartRequest(
            customer_email=validated_data["customer_email"],
            lines=[
                CartLineInput(
                    product_id=item["product_id"],
                    quantity=item["quantity"],
                )
                for item in validated_data["items"]
            ],
        )

        try:
            data = self.service.execute(payload)
        except ProductNotAvailableError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except DuplicatedCartItemError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_409_CONFLICT)
        except ValidationError as exc:
            return Response({"error": exc.messages}, status=status.HTTP_400_BAD_REQUEST)

        return Response(CartOutputSerializer(instance=data).data, status=status.HTTP_201_CREATED)
