from django.urls import path
from django.views.generic import RedirectView

from .views import HomeView

app_name = 'core'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('home/', RedirectView.as_view(pattern_name='core:home', permanent=True), name='home-redirect'),
]
