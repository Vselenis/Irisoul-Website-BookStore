from django.urls import path

from .models import Product
from .views import ProductListView, ProductDetailView

app_name = 'products'

urlpatterns = [
    path(
        'books/',
        ProductListView.as_view(product_type=Product.ProductType.BOOK, heading='Books'),
        name='book-list',
    ),

    path(
        'books/<slug:slug>/',
        ProductDetailView.as_view(product_type=Product.ProductType.BOOK),
        name='book-detail',
    ),
]
