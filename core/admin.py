from django.contrib import admin
from .models import ContactMessage
# Register your models here.


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'phone', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('full_name', 'email', 'phone', 'message')
    date_hierarchy = 'created_at'
    fields = ('full_name', 'email', 'phone', 'message', 'created_at')
    readonly_fields = ('created_at',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False