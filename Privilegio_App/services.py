from django.shortcuts import get_object_or_404
from .models import Producto, Carrito
from .builders import ItemCarritoBuilder
from .factories import ImpuestoFactory


class CarritoService:

    def agregar_producto(self, usuario, producto_id, cantidad):

        producto = get_object_or_404(Producto, id=producto_id)

        carrito, created = Carrito.objects.get_or_create(usuario=usuario)

        builder = ItemCarritoBuilder() \
            .with_carrito(carrito) \
            .with_producto(producto) \
            .with_cantidad(cantidad)

        item = builder.build()
        item.save()

        return item


    def calcular_total(self, usuario):

        carrito = get_object_or_404(Carrito, usuario=usuario)

        total = sum(item.subtotal() for item in carrito.items.all())

        impuesto_service = ImpuestoFactory.get_service()
        impuesto = impuesto_service.calcular(total)

        return total + impuesto
