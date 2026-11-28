from django.urls import path

from .models import Product
from .views import ProductListView, ProductDetailView, FreePDFDownloadView

app_name = 'products'

urlpatterns = [
    path(
        'books/',
        ProductListView.as_view(
            product_type=Product.ProductType.BOOK,
            heading='Books',
            offers = (
                'bundles',
                'deals',
                'free_pdf'
            ),
        ),
        name='book-list',
    ),
    path(
        'books/<slug:slug>/',
        ProductDetailView.as_view(product_type=Product.ProductType.BOOK),
        name='book-detail',
    ),
    path(
        'books/<slug:slug>/download/',
        FreePDFDownloadView.as_view(product_type=Product.ProductType.BOOK),
        name='book-download',
    )
]
