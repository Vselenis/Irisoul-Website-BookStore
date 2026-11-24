from io import BytesIO
from django import forms
from django.core.files.base import ContentFile
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, UsernameField
from django.utils.translation import gettext_lazy as _
from .models import User

from PIL import Image, ImageOps


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


class CustomerDetailsForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'phone', 'country', 'city', 'postcode', 'address')
        labels = {
            'first_name': 'First Name',
            'last_name': 'Second Name',
            'phone': 'Contact Number',
            'country': 'Country',
            'city': 'City',
            'postcode': 'Postcode',
            'address': 'Full Address',
        }
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Second Name'}),
            'phone': forms.TextInput(attrs={'type': 'tel', 'class': 'form-control', 'placeholder': '+359 88 123 4567'}),
            'country': forms.Select(attrs={'class': 'form-control default-select'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City Name'}),
            'postcode': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '1000'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Street, number, building, apartment'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['country'].choices = [('', 'Select Country')] + list(self.fields['country'].choices)[1:]




class ProfileForm(CustomerDetailsForm):
    AVATAR_MAX_SIZE = 5 * 1024 * 1024
    AVATAR_FORMATS = {'JPEG', 'PNG', 'WEBP'}
    AVATAR_SIZE = (400, 400)

    class Meta(CustomerDetailsForm.Meta):
        fields = ('avatar',) + CustomerDetailsForm.Meta.fields
        labels = {**CustomerDetailsForm.Meta.labels, 'avatar': 'Profile Picture'}
        widgets = {
            **CustomerDetailsForm.Meta.widgets,
            'avatar': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/jpeg,image/png,image/webp'}),
        }


    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if not self.files.get('avatar'):
            return avatar
        if avatar.size > self.AVATAR_MAX_SIZE:
            raise forms.ValidationError('The photo must be 5 MB or smaller.')
        if avatar.image.format not in self.AVATAR_FORMATS:
            raise forms.ValidationError('Upload a JPG, PNG or WebP image.')
        avatar.seek(0)
        with Image.open(avatar) as source:
            image = ImageOps.exif_transpose(source)
            if image.mode in ('RGBA', 'LA', 'P'):
                image = image.convert('RGBA')
                background = Image.new('RGB', image.size, (255, 255, 255))
                background.paste(image, mask=image.getchannel('A'))
                image = background
            else:
                image = image.convert('RGB')
            image = ImageOps.fit(image,self.AVATAR_SIZE,Image.Resampling.LANCZOS)
            buffer = BytesIO()
            image.save(buffer, 'JPEG', quality=85, optimize=True)
        return ContentFile(buffer.getvalue(), name='avatar.jpg')