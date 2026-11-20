from django.shortcuts import render
from django.views.generic import TemplateView, CreateView
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from .forms import ContactForm
# Create your views here.

class HomeView(TemplateView):
    template_name = 'core/home.html'

class AboutView(TemplateView):
    template_name = 'core/about.html'

class TermsPrivacyView(TemplateView):
    template_name = 'core/terms_privacy.html'

class ContactView(SuccessMessageMixin, CreateView):
    form_class = ContactForm
    template_name = 'core/contact.html'
    success_url = reverse_lazy('core:contact')
    success_message = 'Thank you, your message has been sent.'
