from typing import Any, cast

from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from ..domain.builders import CartLineInput
from ..exceptions import DuplicatedCartItemError, ProductNotAvailableError
from .serializers import CartOutputSerializer, CreateCartInputSerializer
from ..services import CreateCartRequest, ShoppingCartService


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
