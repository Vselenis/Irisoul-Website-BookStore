from django.contrib import admin

from .models import Author, Book, Category, Product, Publisher, Review

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
    list_display = ('title', 'product_type', 'price', 'promo_price', 'created_at')
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
        'image',
        'categories',
        'created_at',
        'updated_at',
    )
    readonly_fields = ('created_at', 'updated_at')
    inlines = (BookInline,)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'created_at')
    list_filter = ('rating',)
    search_fields = ('product__title', 'user__email', 'user__username', 'comment')
    autocomplete_fields = ('product', 'user')
    readonly_fields = ('created_at',)
