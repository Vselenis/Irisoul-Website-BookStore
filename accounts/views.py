from django.conf import settings

from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView

from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect, render, resolve_url
from django.urls import reverse_lazy
from django.views.generic import CreateView,UpdateView
from django.utils.http import url_has_allowed_host_and_scheme

from .forms import LoginForm, RegistrationForm, ProfileForm
from .models import User
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

    def get_redirect_url(self):
        next_url=self.request.POST.get('next', self.request.GET.get('next', ''))
        if url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return next_url
        return ''

    def get_success_url(self):
        return  self.get_redirect_url() or resolve_url(settings.LOGIN_REDIRECT_URL)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['next'] = self.get_redirect_url()
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response

class ProfileView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    form_class=ProfileForm
    template_name='accounts/profile.html'
    context_object_name='profile_user'
    success_url=reverse_lazy('accounts:profile')
    success_message='Your profile has been updated.'


    def get_object(self, queryset=None):
        user = User.objects.get(pk=self.request.user.pk)
        self.previous_avatar = user.avatar.name
        return user


    def form_valid(self, form):
        response = super().form_valid(form)
        if self.previous_avatar and self.previous_avatar != self.object.avatar.name:
            self.object.avatar.storage.delete(self.previous_avatar)
        return response
