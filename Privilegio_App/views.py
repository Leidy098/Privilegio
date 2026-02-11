from django.shortcuts import render

# Create your views here.
from django.views import View
from django.http import JsonResponse
from .services import CarritoService

from django.views.generic import TemplateView

class AgregarProductoView(View):

    def post(self, request, *args, **kwargs):

        producto_id = request.POST.get("producto_id")
        cantidad = int(request.POST.get("cantidad"))

        service = CarritoService()
        item = service.agregar_producto(
            request.user,
            producto_id,
            cantidad
        )

        return JsonResponse({
            "mensaje": "Producto agregado",
            "producto": item.producto.nombre,
            "cantidad": item.cantidad
        })

class VerCarritoView(TemplateView):
    template_name = "carrito.html"

class HomeView(TemplateView):
    template_name = "Privilegio_App/home.html"
