from django.urls import path

from .views import CartAddView, CartRemoveView, CartUpdateView, CartView

app_name = 'cart'

urlpatterns = [
    path('cart/', CartView.as_view(), name='cart'),
    path('cart/add/<int:product_id>/', CartAddView.as_view(), name='add'),
    path('cart/remove/<int:product_id>/', CartRemoveView.as_view(), name='remove'),
    path('cart/update/<int:product_id>/', CartUpdateView.as_view(), name='update'),
]
