from django.conf import settings

from django.contrib import messages

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import redirect_to_login
from django.http import JsonResponse


from django.shortcuts import get_object_or_404, redirect, resolve_url
from django.urls import reverse

from django.views import View
from django.views.generic import ListView

from products.models import Product

from .forms import QUANTITY_ERROR, QuantityForm
from .models import WishlistItem

# Create your views here.


class WishlistView(LoginRequiredMixin, ListView):
    template_name= 'wishlist/wishlist.html'
    context_object_name= 'items'

    def get_queryset(self):
        return self.request.user.wishlist_items.select_related('product')


class WishlistActionMixin(LoginRequiredMixin):
    http_method_names = ['post']

    def is_ajax(self):
        return self.request.headers.get('x-requested-with') == 'XMLHttpRequest'

    def handle_no_permission(self):
        if self.is_ajax():
            return JsonResponse({'login_url': resolve_url(settings.LOGIN_URL)}, status=401)
        return redirect_to_login(reverse('wishlist:wishlist'))

    def state_response(self, in_wishlist):
        return JsonResponse({
            'in_wishlist': in_wishlist,
            'count': self.request.user.wishlist_items.count(),
        })



class WishlistAddView(WishlistActionMixin, View):
    def post(self, request, product_id):
        product = get_object_or_404(Product, pk=product_id)
        form = QuantityForm({'quantity': request.POST.get('quantity', 1)})
        if not form.is_valid():
            return JsonResponse({'error': form.errors['quantity'][0]}, status=400)
        WishlistItem.objects.get_or_create(
            user=request.user,
            product=product,
            defaults={'quantity': form.cleaned_data['quantity']},
        )
        return self.state_response(True)


class WishlistRemoveView(WishlistActionMixin, View):
    def post(self, request, product_id):
        item =request.user.wishlist_items.select_related('product').filter(product_id=product_id).first()
        if item:
            item.delete()
        if self.is_ajax():
            return self.state_response(False)
        if item:
            messages.success(request, f'"{item.product.title}" was removed from your wishlist.')
        return redirect('wishlist:wishlist')


class WishlistUpdateView(WishlistActionMixin, View):
    def post(self, request):
        changed = []
        invalid = False
        for item in request.user.wishlist_items.all():
            value = request.POST.get(f'quantity-{item.pk}')
            if value is None:
                continue
            form = QuantityForm({'quantity': value})
            if not form.is_valid():
                invalid = True
                continue
            if form.cleaned_data['quantity'] != item.quantity:
                item.quantity = form.cleaned_data['quantity']
                changed.append(item)
        if changed:
            WishlistItem.objects.bulk_update(changed, ['quantity'])
        if invalid:
            messages.error(request, f'Some quantities were not saved. {QUANTITY_ERROR}')
        else:
            messages.success(request, 'Your wishlist has been updated.')
        return redirect('wishlist:wishlist')
