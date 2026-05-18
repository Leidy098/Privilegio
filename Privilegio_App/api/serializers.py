from rest_framework import serializers


class CartItemInputSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1)


class CreateCartInputSerializer(serializers.Serializer):
    customer_email = serializers.EmailField()
    items = CartItemInputSerializer(many=True, allow_empty=False)


class CartItemOutputSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField()
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    line_total = serializers.DecimalField(max_digits=10, decimal_places=2)


class CartOutputSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    customer_email = serializers.EmailField()
    status = serializers.CharField()
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2)
    tax = serializers.DecimalField(max_digits=10, decimal_places=2)
    total = serializers.DecimalField(max_digits=10, decimal_places=2)
    items = CartItemOutputSerializer(many=True)
