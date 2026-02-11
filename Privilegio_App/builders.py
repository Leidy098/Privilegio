from .models import ItemCarrito

class ItemCarritoBuilder:

    def __init__(self):
        self._carrito = None
        self._producto = None
        self._cantidad = 0

    def with_carrito(self, carrito):
        self._carrito = carrito
        return self

    def with_producto(self, producto):
        self._producto = producto
        return self

    def with_cantidad(self, cantidad):
        self._cantidad = cantidad
        return self

    def build(self):
        if self._producto.stock < self._cantidad:
            raise ValueError("Stock insuficiente")

        if self._cantidad <= 0:
            raise ValueError("Cantidad inválida")

        return ItemCarrito(
            carrito=self._carrito,
            producto=self._producto,
            cantidad=self._cantidad
        )
