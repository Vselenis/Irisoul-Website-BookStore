from django.conf import settings

from django.contrib.auth import login
from django.contrib.auth.views import LoginView

from django.shortcuts import redirect, render, resolve_url
from django.views.generic import CreateView

from .forms import LoginForm, RegistrationForm

# Create your views here.


class UserLoginView(LoginView):
    template_name = 'accounts/login.html'
    authentication_form = LoginForm
    redirect_authenticated_user=True


class RegisterView(CreateView):
    form_class= RegistrationForm
    template_name= 'accounts/register.html'


    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(self.get_success_url())
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return resolve_url(settings.LOGIN_REDIRECT_URL)


    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response
