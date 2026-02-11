from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.views.generic import TemplateView
from django.views import View

from .services import ShoppingCartService


class HomeView(TemplateView):
    template_name = "Privilegio_App/home.html"


class ShoppingCartCreateView(View):
    service = ShoppingCartService()

    def post(self, request, *args, **kwargs):
        try:
            data = self.service.create_cart_from_raw_body(request.body)
        except (ValidationError, KeyError, TypeError, ValueError) as exc:
            return JsonResponse({"error": str(exc)}, status=400)
        return JsonResponse(data, status=201)
