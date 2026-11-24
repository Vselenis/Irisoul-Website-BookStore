from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import AdminUserCreationForm, UserChangeForm

from django.utils.translation import gettext_lazy as _

from .models import User

# Register your models here.


class UserAdminCreationForm(AdminUserCreationForm):


    class Meta(AdminUserCreationForm.Meta):
        model = User
        fields = ('email', 'username')


class UserAdminChangeForm(UserChangeForm):

    class Meta(UserChangeForm.Meta):
        model = User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form= UserAdminChangeForm
    add_form =UserAdminCreationForm
    fieldsets =(
        (None, {'fields': ('email', 'username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name','avatar')}),
        (_('Customer details'), {'fields': ('phone', 'country', 'city', 'postcode', 'address')}),
    ) + BaseUserAdmin.fieldsets[2:]
    add_fieldsets = ((None,{'classes': ('wide',),'fields': ('email', 'username', 'usable_password', 'password1', 'password2'),},),)
    list_display = ('email', 'username', 'first_name', 'last_name', 'is_staff')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('email',)

