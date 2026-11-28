from decimal import Decimal

SHIPPING_COST = Decimal('10.00')
FREE_SHIPPING_THRESHOLD = Decimal('100.00')


class CartSummary:
    def __init__(self, items):
        self.items = list(items)
        self.purchasable_items = [item for item in self.items if item.product.is_purchasable]
        self.subtotal = sum((item.total for item in self.purchasable_items), Decimal('0.00'))
        self.free_shipping = self.subtotal >= FREE_SHIPPING_THRESHOLD
        self.shipping = Decimal('0.00') if self.free_shipping else SHIPPING_COST
        self.total = self.subtotal + self.shipping
        self.free_shipping_threshold = FREE_SHIPPING_THRESHOLD


    @classmethod
    def for_user(cls, user):
        return cls(user.cart_items.select_related('product__bundle'))