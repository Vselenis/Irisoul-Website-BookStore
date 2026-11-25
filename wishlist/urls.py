from django.urls import path

from .views import WishlistAddView, WishlistRemoveView, WishlistUpdateView, WishlistView

app_name = 'wishlist'

urlpatterns = [
    path('wishlist/', WishlistView.as_view(), name='wishlist'),
    path('wishlist/update/', WishlistUpdateView.as_view(), name='update'),
    path('wishlist/add/<int:product_id>/', WishlistAddView.as_view(), name='add'),
    path('wishlist/remove/<int:product_id>/', WishlistRemoveView.as_view(), name='remove'),
]
