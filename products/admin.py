from django.contrib import admin
from django import forms
from .models import Author, Book, Category, Product, Publisher, Review,  Bundle, BundleProduct, FreePDFProduct

from django.forms.models import BaseInlineFormSet
# Register your models here.


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


class BookInline(admin.StackedInline):
    model = Book
    min_num = 1
    max_num = 1
    can_delete = False
    autocomplete_fields = ('authors', 'publisher')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'product_type', 'price', 'promo_price', 'promo_start', 'promo_end','created_at')
    list_filter = ('product_type', 'categories')
    search_fields = ('title', 'book__isbn', 'book__authors__name')
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ('categories',)
    fields = (
        'product_type',
        'title',
        'slug',
        'description',
        'price',
        'promo_price',
        'promo_start',
        'promo_end',
        'image',
        'categories',
        'created_at',
        'updated_at',
    )
    readonly_fields = ('created_at', 'updated_at')
    inlines = (BookInline,)
    def get_queryset(self, request):
        return super().get_queryset(request).regular()

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'created_at')
    list_filter = ('rating',)
    search_fields = ('product__title', 'user__email', 'user__username', 'comment')
    autocomplete_fields = ('product', 'user')
    readonly_fields = ('created_at',)

class BundleInlineForm(forms.ModelForm):
    class Meta:
        model = Bundle
        fields = (
            'items',
            'discount_percent',
            'is_active',
            'available_until'
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['items'].queryset = Product.objects.regular().order_by('title')

    def clean_items(self):
        items = self.cleaned_data['items']
        if len(items) < 2:
            raise forms.ValidationError('A bundle must include at least 2 products.')
        return items


class BundleInline(admin.StackedInline):
    model = Bundle
    form = BundleInlineForm
    min_num=1
    max_num=1
    can_delete=False
    filter_horizontal = ('items',)


@admin.register(BundleProduct)
class BundleProductAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'product_type',
        'price',
        'promo_price',
        'bundle_active',
        'bundle_available_until',
        'available'
    )
    list_filter = ('product_type', 'bundle__is_active')
    search_fields = ('title',)
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ('categories',)
    fields = (
        'product_type',
        'title',
        'slug',
        'description',
        'image',
        'categories',
        'price',
        'promo_price',
        'saving',
        'created_at',
        'updated_at',
    )
    readonly_fields = ('price', 'promo_price', 'saving', 'created_at', 'updated_at')
    inlines = (BundleInline,)

    def get_queryset(self, request):
        return super().get_queryset(request).bundles().select_related('bundle')

    def save_model(self, request, obj, form, change):
        if obj.price is None:
            obj.price = 0
        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        bundle = form.instance.bundle_details
        if bundle is not None:
            bundle.refresh_prices()

    @admin.display(description='original total (€)')
    def price(self, obj):
        return obj.price

    @admin.display(description='bundle price (€)')
    def promo_price(self, obj):
        return obj.promo_price

    @admin.display(description='customer saves (€)')
    def saving(self, obj):
        if obj.pk is None or obj.promo_price is None:
            return '-'
        return obj.price - obj.promo_price

    @admin.display(description='active', boolean=True)
    def bundle_active(self, obj):
        return obj.bundle.is_active

    @admin.display(description='available until')
    def bundle_available_until(self, obj):
        return obj.bundle.available_until

    @admin.display(description='available now', boolean=True)
    def available(self, obj):
        return obj.bundle.is_available


class OptionalBookInline(BookInline):
    min_num=0
    verbose_name = 'book details (optional)'


@admin.register(FreePDFProduct)
class FreePDFProductAdmin(admin.ModelAdmin):
    list_display = ('title','product_type','created_at')
    list_filter = ('product_type','categories')
    search_fields = ('title','book__authors__name')
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ('categories',)
    fields = (
        'product_type',
        'title',
        'slug',
        'description',
        'image',
        'free_pdf',
        'categories',
        'created_at',
        'updated_at',
    )
    readonly_fields = ('created_at', 'updated_at')
    inlines = (OptionalBookInline,)

    def get_queryset(self, request):
        return super().get_queryset(request).free_pdfs()

    def get_form(self, request, obj= None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['free_pdf'].required=True
        return form

    def save_model(self, request, obj, form, change):
        obj.price = 0
        obj.promo_price=None
        obj.promo_start=None
        obj.promo_end=None
        super().save_model(request, obj, form, change)


class BundleInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        product_type = self.instance.product_type
        for form in self.forms:
            items = getattr(form, 'cleaned_data', {}).get('items')
            if items and any(item.product_type != product_type for item in items):
                form.add_error('items', 'All included products must be of the same type as the bundle.')

