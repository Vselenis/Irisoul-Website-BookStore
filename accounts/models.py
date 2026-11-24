import uuid
from django.contrib.auth.models import AbstractUser

from django.contrib.auth.models import UserManager as DjangoUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _

from django.core.validators import RegexValidator

# Create your models here.
class UserManager(DjangoUserManager):
    @classmethod
    def normalize_email(cls, email):
        return super().normalize_email(email).lower()

    def get_by_natural_key(self, username):
        return self.get(**{f'{self.model.USERNAME_FIELD}__iexact': username})

EU_COUNTRIES = [
    ('AT', 'Austria'),
    ('BE', 'Belgium'),
    ('BG', 'Bulgaria'),
    ('HR', 'Croatia'),
    ('CY', 'Cyprus'),
    ('CZ', 'Czechia'),
    ('DK', 'Denmark'),
    ('EE', 'Estonia'),
    ('FI', 'Finland'),
    ('FR', 'France'),
    ('DE', 'Germany'),
    ('GR', 'Greece'),
    ('HU', 'Hungary'),
    ('IE', 'Ireland'),
    ('IT', 'Italy'),
    ('LV', 'Latvia'),
    ('LT', 'Lithuania'),
    ('LU', 'Luxembourg'),
    ('MT', 'Malta'),
    ('NL', 'Netherlands'),
    ('PL', 'Poland'),
    ('PT', 'Portugal'),
    ('RO', 'Romania'),
    ('SK', 'Slovakia'),
    ('SI', 'Slovenia'),
    ('ES', 'Spain'),
    ('SE', 'Sweden'),
]

phone_validator = RegexValidator(
    r'^[0-9+()\- ]{6,20}$',
    'Enter a valid phone number: 6 to 20 characters, using digits, spaces and + - ( ).',
)


def avatar_upload_to(instance, filename):
    return f'avatars/{uuid.uuid4().hex}.jpg'

class User(AbstractUser):
    email = models.EmailField(_('email address'), unique=True)
    avatar = models.ImageField(_('profile picture'),upload_to=avatar_upload_to,blank=True)
    phone =models.CharField(_('contact number'),max_length=20,blank=True,validators=[phone_validator])
    country = models.CharField(_('country'),max_length=2,choices=EU_COUNTRIES,blank=True)
    city = models.CharField(_('city'),max_length=100,blank=True)
    postcode= models.CharField(_('postcode'),max_length=20,blank=True)
    address= models.CharField(_('full address'),max_length=255,blank=True)

    objects = UserManager()

    USERNAME_FIELD='email'
    REQUIRED_FIELDS= ['username']

