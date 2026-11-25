from django.contrib import admin
from .models import WishlistItem

# Register your models here.


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'quantity', 'created_at')
    list_filter = ('created_at',)
    list_select_related = ('user', 'product')
    search_fields = ('user__email', 'user__username', 'product__title')
    date_hierarchy = 'created_at'
    fields = ('user', 'product', 'quantity', 'created_at')
    readonly_fields = ('created_at',)


    def has_add_permission(self, request):
        return False


    def has_change_permission(self, request, obj=None):
        return False
