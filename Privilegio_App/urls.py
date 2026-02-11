from django.urls import path
from .views import AgregarProductoView

urlpatterns = [
    path('agregar/', AgregarProductoView.as_view(), name='agregar_producto'),
]
