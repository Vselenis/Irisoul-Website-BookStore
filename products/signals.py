from django.db.models.signals import m2m_changed, post_delete, post_save, pre_delete

from django.dispatch import receiver

from .models import Bundle, Product


def refresh_bundles(bundle_ids):
    for bundle in Bundle.objects.filter(pk__in=bundle_ids).select_related('product'):
        bundle.refresh_prices()


@receiver(post_save, sender= Product)
def product_saved(sender, instance, raw=False, **kwargs):
    if raw:
        return
    refresh_bundles(instance.in_bundles.values_list('pk',flat=True))


@receiver(pre_delete,sender=Product)
def product_deleting(sender, instance, **kwargs):
    instance._bundle_ids = list(instance.in_bundles.values_list('pk',flat=True))


@receiver(post_delete,sender=Product)
def product_deleted(sender, instance, **kwargs):
    refresh_bundles(getattr(instance, '_bundle_ids', []))


@receiver(post_save,sender=Bundle)
def bundle_saved(sender, instance, raw=False, **kwargs):
    if raw:
        return
    instance.refresh_prices()


@receiver(m2m_changed,sender=Bundle.items.through)
def bundle_items_changed(sender, instance, action, reverse, pk_set, **kwargs):
    if action not in ('post_add', 'post_remove', 'post_clear'):
        return
    if reverse:
        refresh_bundles(pk_set or [])
    else:
        instance.refresh_prices()
