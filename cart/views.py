from django.conf import settings

from django.contrib import messages

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import redirect_to_login
from django.http import JsonResponse


from django.shortcuts import get_object_or_404, redirect, resolve_url
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from django.views import View
from django.views.generic import TemplateView

from products.models import Product
from wishlist.forms import QUANTITY_ERROR, QuantityForm
from wishlist.models import MAX_QUANTITY

from django.db.models import F, Value
from django.db.models.functions import Least

from .models import CartItem
from .summary import CartSummary

# Create your views here.


class CartView(LoginRequiredMixin, TemplateView):
    template_name= 'cart/cart.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        summary = CartSummary.for_user(self.request.user)
        context['cart_summary'] = summary
        context['items'] = summary.items
        return context


class CartActionMixin(LoginRequiredMixin):
    http_method_names = ['post']

    def is_ajax(self):
        return self.request.headers.get('x-requested-with') == 'XMLHttpRequest'

    def get_next_url(self):
        next_url = self.request.POST.get('next', '')
        if url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return next_url
        return ''


    def handle_no_permission(self):
        if self.is_ajax():
            return JsonResponse({'login_url': resolve_url(settings.LOGIN_URL)}, status=401)
        return redirect_to_login(self.get_next_url() or reverse('cart:cart'))


class CartAddView(CartActionMixin, View):
    def post(self, request, product_id):
        product = get_object_or_404(Product, pk=product_id)
        form = QuantityForm({'quantity': request.POST.get('quantity', 1)})
        if not form.is_valid():
            messages.error(request, QUANTITY_ERROR)
            return redirect('cart:cart')
        quantity = form.cleaned_data['quantity']
        item, created = CartItem.objects.get_or_create(
            user=request.user,
            product=product,
            defaults={'quantity': quantity},
        )
        if created:
            messages.success(request, f'"{product.title}" was added to your shopping cart.')
            return redirect('cart:cart')
        CartItem.objects.filter(pk=item.pk).update(
            quantity=Least(F('quantity') + quantity, Value(MAX_QUANTITY)),
        )
        if item.quantity + quantity > MAX_QUANTITY:
            messages.warning(
                request,
                f'"{product.title}" is in your shopping cart. The maximum quantity per book is {MAX_QUANTITY}.',
            )
        else:
            messages.success(request, f'"{product.title}" was added to your shopping cart.')
        return redirect('cart:cart')


class CartRemoveView(CartActionMixin, View):
    def post(self, request, product_id):
        item = request.user.cart_items.select_related('product').filter(product_id=product_id).first()
        if item:
            item.delete()
        next_url = self.get_next_url()
        if next_url:
            return redirect(next_url)
        if item:
            messages.success(request, f'"{item.product.title}" was removed from your shopping cart.')
        return redirect('cart:cart')



class CartUpdateView(CartActionMixin, View):
    def post(self, request, product_id):
        form = QuantityForm({'quantity': request.POST.get('quantity')})
        if not form.is_valid():
            return JsonResponse({'error': form.errors['quantity'][0]}, status=400)
        updated = request.user.cart_items.filter(product_id=product_id).update(
            quantity=form.cleaned_data['quantity'],
        )

        if not updated:
            return JsonResponse({'error': 'This book is no longer in your shopping cart.'}, status=404)
        summary = CartSummary.for_user(request.user)
        item = next(item for item in summary.items if item.product_id == product_id)
        return JsonResponse({
            'quantity': item.quantity,
            'row_total': f'{item.total:.2f}',
            'subtotal': f'{summary.subtotal:.2f}',
            'shipping': f'{summary.shipping:.2f}',
            'free_shipping': summary.free_shipping,
            'total': f'{summary.total:.2f}',
        })
