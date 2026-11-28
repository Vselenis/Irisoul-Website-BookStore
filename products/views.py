from math import ceil, floor
from django.db import IntegrityError,transaction
from django.db.models import Avg, Count, Exists, Max, Min, OuterRef,Prefetch,Q
from django.db.models.functions import Coalesce, Round
from django.shortcuts import redirect, render,get_object_or_404
from django.urls import reverse
from django.views.generic import ListView, DetailView
from django.contrib.auth.views import redirect_to_login
from django.http import FileResponse, Http404
from django.utils import timezone
from django.views import View

from .forms import ProductFilterForm,ReviewForm
from .models import Category, Product,Review,promo_active_q


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
    offers = ()
    offer_labels = {
        'bundles': 'Christmas Bundles',
        'deals': 'December Deals',
        'free_pdf': 'Free PDF',
    }
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
        self.offer_choices = [(key, self.offer_labels[key]) for key in self.offers]
        form = ProductFilterForm(request.GET, categories=self.categories, offers=self.offer_choices)
        form.is_valid()
        self.filters = form.cleaned_data
        self.sort = self.filters.get('sort') or 'newest'
        return super().get(request, *args, **kwargs)


    def get_categories(self):
        return list(Category.objects.filter(products__product_type=self.product_type).distinct())

    def get_base_queryset(self):
        return Product.objects.filter(
            product_type=self.product_type
        ).available().with_effective_price()

    def get_offer_filter(self, offers):
        conditions = {
            'bundles': Q(bundle__isnull=False),
            'deals': promo_active_q(timezone.localdate()) & Q(bundle__isnull=True),
            'free_pdf': ~Q(free_pdf=''),
        }
        combined = Q()
        for offer in offers:
            combined |= conditions[offer]
        return combined

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
        if filters.get('offer'):
            queryset = queryset.filter(self.get_offer_filter(filters['offer']))
        return (
            queryset.select_related('book__publisher', 'bundle')
            .prefetch_related('categories', 'book__authors', 'bundle__items')
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
            'offer_choices': self.offer_choices,
            'selected_offers': filters.get('offer') or [],
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


class ProductDetailView(DetailView):
    template_name = 'products/product_detail.html'
    context_object_name = 'product'
    product_type = None
    related_count = 3


    def get_queryset(self):
        return (
            with_ratings(Product.objects.filter(product_type=self.product_type))
            .select_related('book__publisher','bundle')
            .prefetch_related(
                'categories',
                'book__authors',
                'bundle__items',
                Prefetch('reviews', queryset=Review.objects.select_related('user')),
            )
        )


    def get_related_products(self):
        category_ids = [category.pk for category in self.object.categories.all()]
        if not category_ids:
            return []
        return list(
            Product.objects.filter(product_type=self.product_type)
            .available()
            .exclude(pk=self.object.pk)
            .filter(
                Exists(
                    Product.categories.through.objects.filter(
                        product=OuterRef('pk'),
                        category_id__in=category_ids,
                    )
                )
            )
            .select_related('bundle')
            .prefetch_related('categories')
            .order_by('?')[:self.related_count]
        )
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.is_available:
            return redirect('core:home')
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def has_reviewed(self):
        user = self.request.user
        return user.is_authenticated and any(review.user_id == user.pk for review in self.object.reviews.all())


    def get_context_data(self, **kwargs):
        kwargs.setdefault('form', ReviewForm())
        kwargs.setdefault('login_required', False)
        kwargs.setdefault('already_reviewed', self.has_reviewed())
        context = super().get_context_data(**kwargs)
        context.update({
            'reviews': self.object.reviews.all(),
            'related_products': self.get_related_products(),
            'list_url': reverse(f'products:{self.object.product_type}-list'),
        })
        return context


    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.is_available:
            return redirect('core:home')
        if not request.user.is_authenticated:
            form = ReviewForm(initial={
                'rating': request.POST.get('rating'),
                'comment': request.POST.get('comment', ''),
            })
            return self.render_to_response(self.get_context_data(form=form, login_required=True))
        if self.has_reviewed():
            return self.render_to_response(self.get_context_data())
        form = ReviewForm(request.POST)
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(form=form))
        form.instance.product=self.object
        form.instance.user=request.user
        try:
            with transaction.atomic():
                form.save()
        except IntegrityError:
            return self.render_to_response(self.get_context_data(already_reviewed=True))
        return redirect(f'{self.object.get_absolute_url()}#reviews')


class FreePDFDownloadView(View):
    product_type=None

    def get(self, request, slug):
        product=get_object_or_404(Product.objects.free_pdfs(), product_type=self.product_type, slug=slug)
        if not request.user.is_authenticated:
            return redirect_to_login(product.get_absolute_url())
        try:
            file=product.free_pdf.open('rb')
        except FileNotFoundError:
            raise Http404('The PDF file is not available.')
        return FileResponse(file, as_attachment=True, filename=f'{product.slug}.pdf', content_type='application/pdf')