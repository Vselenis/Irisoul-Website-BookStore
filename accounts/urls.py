from django.contrib.auth.views import LogoutView

from django.urls import path

from .views import RegisterView, UserLoginView, ProfileView

app_name = 'accounts'

urlpatterns = [
    path('login/', UserLoginView.as_view(), name = 'login'),
    path('register/', RegisterView.as_view(),name = 'register'),
    path('logout/', LogoutView.as_view(), name = 'logout'),
    path('profile/', ProfileView.as_view(), name = 'profile'),
]
