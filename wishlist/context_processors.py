from django.utils.functional import SimpleLazyObject


def wishlist(request):
    user = request.user

    if not user.is_authenticated:
        return {'wishlist_product_ids': frozenset()}

    return {
        'wishlist_product_ids': SimpleLazyObject(
            lambda: frozenset(user.wishlist_items.values_list('product_id',flat=True))
        ),
    }
