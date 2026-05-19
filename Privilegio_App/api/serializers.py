from rest_framework import serializers

MEASUREMENT_FIELDS = {
    "shirt":     ["chest", "waist", "shoulders", "neck"],
    "pants":     ["waist", "hips", "leg_length"],
    "outerwear": ["chest", "waist", "shoulders", "hips", "arm_length"],
}
OPTIONAL_FIELDS = {
    "shirt":     ["arm_length"],
    "pants":     ["thigh"],
    "outerwear": ["total_length"],
}


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


class SizeRecommendationInputSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(min_value=1)
    measurements = serializers.DictField(
        child=serializers.FloatField(min_value=20, max_value=200),
        allow_empty=False,
    )


class SizeRecommendationOutputSerializer(serializers.Serializer):
    out_of_range = serializers.BooleanField()
    recommended_size = serializers.CharField(allow_null=True)
    fit = serializers.CharField(allow_null=True)
    message = serializers.CharField()
    conflict = serializers.BooleanField()
    suggest_next_size = serializers.CharField(allow_null=True)
