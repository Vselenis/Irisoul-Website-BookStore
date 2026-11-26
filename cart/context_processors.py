from django.utils.functional import SimpleLazyObject

from .summary import CartSummary


def cart(request):
    user = request.user
    if not user.is_authenticated:
        return {'cart_summary': None}
    return {'cart_summary': SimpleLazyObject(lambda: CartSummary.for_user(user))}
