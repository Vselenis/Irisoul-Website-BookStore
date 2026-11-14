from django import forms

from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, UsernameField

from django.utils.translation import gettext_lazy as _
from .models import User


class RegistrationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control',
                                               'placeholder': 'Your Username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control',
                                             'placeholder': 'Your Email address'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.pop('autofocus',None)
        self.fields['username'].widget.attrs['autofocus'] = True
        self.fields['password1'].widget.attrs.update({'class': 'form-control',
                                                      'placeholder': 'Type Password'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control',
                                                      'placeholder': 'Confirm Password'})


class LoginForm(AuthenticationForm):
    username = UsernameField( widget=forms.EmailInput(attrs={'autofocus': True,
                                                             'class': 'form-control',
                                                             'placeholder': 'Your Email Id'}))

    password = forms.CharField(
        label=_('Password'),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'current-password',
            'class': 'form-control',
            'placeholder': 'Type Password'}),
    )
