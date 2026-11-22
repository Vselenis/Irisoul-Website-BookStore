from django.contrib import admin
from .models import Category, Comment, Post, Tag

# Register your models here.
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display =('name', 'slug')
    search_fields =('name',)
    prepopulated_fields = {
        'slug': ('name',)
    }


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display =('name', 'slug')
    search_fields = ('name',)
    prepopulated_fields ={
        'slug': ('name',)
    }


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'author', 'is_published', 'published_at')
    list_filter = ('is_published', 'category', 'tags')
    search_fields = ('title', 'content')
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ('tags',)
    date_hierarchy = 'published_at'
    readonly_fields = ('author',)


    def save_model(self, request, obj, form, change):
        if not obj.author_id:
            obj.author = request.user
        super().save_model(request, obj, form, change)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display=('post', 'user', 'is_reply', 'created_at')
    list_filter =('created_at',)
    list_select_related =('post', 'user')
    search_fields =('content', 'user__username', 'post__title')
    fields =('post', 'user', 'parent', 'content', 'created_at')
    readonly_fields =('created_at',)


    @admin.display(boolean=True, description='Reply')
    def is_reply(self, obj):
        return obj.parent_id is not None


    def has_add_permission(self, request):
        return False


    def has_change_permission(self, request, obj=None):
        return False
