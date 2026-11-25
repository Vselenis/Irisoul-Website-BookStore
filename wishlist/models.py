from django.db import models
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator

from django.db.models import Q

# Create your models here.
MAX_QUANTITY = 100


class WishlistItem(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wishlist_items',
    )

    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='wishlist_items',
    )

    quantity = models.PositiveSmallIntegerField(
        default= 1,
        validators=[MinValueValidator(1), MaxValueValidator(MAX_QUANTITY)],
    )
    created_at = models.DateTimeField(auto_now_add=True)


    class Meta:
        ordering = ['-created_at', '-pk']
        constraints = [models.UniqueConstraint(
                fields=['user', 'product'],
                name='wishlist_item_unique_user_product',
            ),
            models.CheckConstraint(
                condition=Q(quantity__gte=1)&Q(quantity__lte=MAX_QUANTITY),
                name='wishlist_item_quantity_range',
                violation_error_message=f'Quantity must be from 1 to {MAX_QUANTITY}.',
            ),
        ]

    def __str__(self):
        return f'{self.user} - {self.product}'


    @property
    def total(self):
        return self.product.current_price * self.quantity
