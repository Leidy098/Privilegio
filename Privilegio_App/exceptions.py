class ProductNotAvailableError(Exception):
    def __init__(self, product_id: int) -> None:
        self.product_id = product_id
        super().__init__(f"Product {product_id} is not available.")


class DuplicatedCartItemError(Exception):
    def __init__(self, product_id: int) -> None:
        self.product_id = product_id
        super().__init__(f"Product {product_id} is duplicated in the cart.")
