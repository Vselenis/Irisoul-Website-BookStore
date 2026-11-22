from django.urls import path

from .views import PostDetailView, PostListView

app_name = 'blog'

urlpatterns = [
    path('blog/', PostListView.as_view(), name='post-list'),
    path('blog/<slug:slug>/', PostDetailView.as_view(), name='post-detail'),
]
