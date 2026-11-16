from math import ceil, floor

from django.db.models import Avg, Count, Exists, Max, Min, OuterRef
from django.db.models.functions import Coalesce, Round
from django.shortcuts import render
from django.views.generic import ListView

from .forms import ProductFilterForm
from .models import Category, Product

# Create your views here.
def with_ratings(queryset):
    return queryset.annotate(
        avg_rating=Coalesce(Avg('reviews__rating'), 0.0),
        review_count=Count('reviews'),
    ).annotate(rating_stars=Round('avg_rating'))


class ProductListView(ListView):
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    product_type = None
    heading = ''
    page_sizes = {'list': 5, 'grid': 10}
    orderings = {
        'newest': ('-created_at', '-pk'),
        'price_asc': ('effective_price', '-created_at', '-pk'),
        'price_desc': ('-effective_price', '-created_at', '-pk'),
        'top_rated': ('-avg_rating', '-review_count', '-created_at', '-pk'),
    }

    def get(self, request, *args, **kwargs):
        self.view_mode= 'grid' if request.GET.get('view') == 'grid' else 'list'
        self.categories= self.get_categories()
        form = ProductFilterForm(request.GET, categories=self.categories)
        form.is_valid()
        self.filters = form.cleaned_data
        self.sort = self.filters.get('sort') or 'newest'
        return super().get(request, *args, **kwargs)


    def get_categories(self):
        return list(Category.objects.filter(products__product_type=self.product_type).distinct())



    def get_base_queryset(self):
        return Product.objects.filter(product_type=self.product_type).annotate(
            effective_price=Coalesce('promo_price', 'price'),
        )


    def get_queryset(self):
        queryset = with_ratings(self.get_base_queryset())
        filters = self.filters
        if filters.get('category'):
            queryset = queryset.filter(
                Exists(
                    Product.categories.through.objects.filter(
                        product=OuterRef('pk'),
                        category__slug__in=filters['category'],
                    )
                )
            )
        if filters.get('min_price') is not None:
            queryset = queryset.filter(effective_price__gte=filters['min_price'])
        if filters.get('max_price') is not None:
            queryset = queryset.filter(effective_price__lte=filters['max_price'])
        if filters.get('min_rating') is not None:
            queryset = queryset.filter(avg_rating__gte=filters['min_rating'])
        if filters.get('max_rating') is not None:
            queryset = queryset.filter(avg_rating__lte=filters['max_rating'])
        if filters.get('promo'):
            queryset = queryset.filter(promo_price__isnull=False)
        return (
            queryset.select_related('book__publisher')
            .prefetch_related('categories', 'book__authors')
            .order_by(*self.orderings[self.sort])
        )
    def get_paginate_by(self, queryset):
        return self.page_sizes[self.view_mode]


    def get_price_bounds(self):
        bounds = self.get_base_queryset().aggregate(
            low=Min('effective_price'),
            high=Max('effective_price'),
        )
        low = floor(bounds['low']) if bounds['low'] is not None else 0
        high = ceil(bounds['high']) if bounds['high'] is not None else 0
        return low, max(high, low + 1)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        price_min, price_max = self.get_price_bounds()
        half = (len(self.categories) + 1) // 2
        filters = self.filters
        context.update({
            'heading': self.heading,
            'view_mode': self.view_mode,
            'sort': self.sort,
            'sort_choices': ProductFilterForm.SORT_CHOICES,
            'filters': filters,
            'category_columns': [self.categories[:half], self.categories[half:]],
            'selected_categories': filters.get('category') or [],
            'price_bounds': {'min': price_min, 'max': price_max},
            'rating_active': filters.get('min_rating') is not None or filters.get('max_rating') is not None,
            'page_range': context['paginator'].get_elided_page_range(
                context['page_obj'].number,
                on_each_side=1,
                on_ends=1,
            ),
            'reset_url': self.request.path + ('?view=grid' if self.view_mode == 'grid' else ''),
        })
        return context
