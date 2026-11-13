from django.contrib.auth.models import AbstractUser

from django.contrib.auth.models import UserManager as DjangoUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _

# Create your models here.
class UserManager(DjangoUserManager):
    @classmethod
    def normalize_email(cls, email):
        return super().normalize_email(email).lower()

    def get_by_natural_key(self, username):
        return self.get(**{f'{self.model.USERNAME_FIELD}__iexact': username})

class User(AbstractUser):
    email = models.EmailField(_('email address'), unique= True)

    objects = UserManager()

    USERNAME_FIELD='email'
    REQUIRED_FIELDS= ['username']

