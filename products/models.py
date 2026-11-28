from decimal import Decimal, ROUND_DOWN

from django.conf import settings
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator,FileExtensionValidator
from django.db import models
from django.db.models import F, Q, Case, DecimalField,When
from django.urls import reverse
from django.utils import timezone

from .storage import protected_storage, validate_pdf
# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=100,unique=True)
    slug = models.SlugField(max_length=120,unique=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name

def promo_active_q(day):
    return (Q(promo_price__isnull=False)
            & (Q(promo_start__isnull=True) | Q(promo_start__lte=day))
            & (Q(promo_end__isnull=True) | Q(promo_end__gte=day)))


def bundle_available_q(day):
    return Q(bundle__is_active=True) \
           & (Q(bundle__available_until__isnull=True) |
              Q(bundle__available_until__gte=day))


class ProductQuerySet(models.QuerySet):
    def available(self):
        return self.filter(Q(bundle__isnull=True) | bundle_available_q(timezone.localdate()))

    def with_effective_price(self):
        return self.annotate(
            effective_price = Case(
                When(promo_active_q(timezone.localdate()), then=F('promo_price')),
                default = F('price'),
                output_field=DecimalField(max_digits=10, decimal_places=2),
            ),
        )


    def bundles(self):
        return self.filter(bundle__isnull=False)

    def deals(self):
        return self.filter(promo_active_q(timezone.localdate()), bundle__isnull=True)

    def free_pdfs(self):
        return self.exclude(free_pdf='')

    def regular(self):
        return self.filter(bundle__isnull=True, free_pdf='')



class Product(models.Model):
    class ProductType(models.TextChoices):
        BOOK = 'book', 'Book'


    product_type = models.CharField(
        max_length=30,
        choices=ProductType.choices,
        default=ProductType.BOOK,
        db_index=True,
    )

    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField()
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
    )
    promo_price= models.DecimalField(
        max_digits= 10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Leave empty when the product is not on promotion.',
    )
    promo_start = models.DateField(
        'sale from',
        null=True,
        blank=True,
        help_text='First day of the promo price. Leave empty to start immediately.',
    )
    promo_end = models.DateField(
        'sale until',
        null=True,
        blank=True,
        help_text='Last day of the promo price. Leave empty for no end date.',
    )
    image = models.ImageField(upload_to='products/')
    free_pdf = models.FileField(
        'free PDF',
        upload_to='free_pdfs/',
        storage=protected_storage,
        blank=True,
        validators=[FileExtensionValidator(['pdf']), validate_pdf],
        help_text='PDF file, up to 50 MB. Downloadable only by logged-in users.',
    )
    categories = models.ManyToManyField(Category, related_name='products')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = ProductQuerySet.as_manager()
    class Meta:
        ordering = ['-created_at']
        constraints= [
            models.CheckConstraint(
                condition=Q(price__gte=0),
                name='product_price_not_negative',
                violation_error_message='Price cannot be negative.',
            ),
            models.CheckConstraint(
                condition=Q(promo_price__isnull=True) | (Q(promo_price__gte=0) & Q(promo_price__lt=F('price'))),
                name='product_promo_price_below_price',
                violation_error_message='Promo price must be lower than the regular price.',
            ),
            models.CheckConstraint(
                condition=Q(promo_start__isnull=True) | Q(promo_end__isnull=True) | Q(promo_end__gte=F('promo_start')),
                name='product_promo_end_after_start',
                violation_error_message='Sale until cannot be earlier than sale from.',
            ),
        ]

    def __str__(self):
        return self.title


    def get_absolute_url(self):
        return reverse(f'products:{self.product_type}-detail', kwargs={'slug': self.slug})

    def clean(self):
        super().clean()
        if self.promo_price is not None and self.price is not None and self.promo_price >= self.price:
            raise ValidationError({'promo_price': 'Promo price must be lower than the regular price.'})
        if self.promo_start and self.promo_end and self.promo_end < self.promo_start:
            raise ValidationError({'promo_end': 'Sale until cannot be earlier than sale from.'})


    def get_download_url(self):
        return reverse(f'products:{self.product_type}-download', kwargs={'slug': self.slug})

    @property
    def has_promo(self):
        if self.promo_price is None:
            return False

        today = timezone.localdate()
        if self.promo_start and self.promo_start > today:
            return False
        if self.promo_end and self.promo_end < today:
            return False
        return True

    @property
    def current_price(self):
        return self.promo_price if self.has_promo else self.price

    @property
    def discount_percent(self):
        if not self.has_promo or not self.price:
            return 0
        return round((self.price - self.promo_price) / self.price * 100)

    @property
    def saving(self):
        return self.price - self.current_price

    @property
    def bundle_details(self):
        try:
            return self.bundle
        except ObjectDoesNotExist:
            return None

    @property
    def book_details(self):
        try:
            return self.book
        except ObjectDoesNotExist:
            return None

    @property
    def is_bundle(self):
        return self.bundle_details is not None

    @property
    def is_free_pdf(self):
        return bool(self.free_pdf)

    @property
    def is_available(self):
        bundle= self.bundle_details
        return bundle is None or bundle.is_available

    @property
    def is_purchasable(self):
        return self.is_available and not self.is_free_pdf


class Bundle(models.Model):
    product =models.OneToOneField(
        Product,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='bundle',
    )
    items =models.ManyToManyField(
        Product,
        related_name='in_bundles',
        verbose_name='included products',
    )
    discount_percent =models.PositiveSmallIntegerField(
        'discount (%)',
        validators=[MinValueValidator(1), MaxValueValidator(90)],
        help_text='The bundle price is the sum of the regular prices minus this percentage.',
    )
    is_active =models.BooleanField('active', default=True)
    available_until =models.DateField(
        null=True,
        blank=True,
        help_text='Last day the bundle is available. Leave empty for no end date.',
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(discount_percent__gte=1) & Q(discount_percent__lte=90),
                name='bundle_discount_between_1_and_90',
                violation_error_message='Discount must be between 1 and 90 percent.',
            ),
        ]


    def __str__(self):
        if self.product_id is None:
            return 'New bundle'
        return str(self.product)

    @property
    def is_available(self):
        if not self.is_active:
            return False
        return self.available_until is None or self.available_until >= timezone.localdate()

    def calculate_prices(self):
        original = sum((item.price for item in self.items.all()), Decimal('0.00'))
        if original <= 0:
            return original, None
        bundle_price = (original * (100 - self.discount_percent) / 100).quantize(Decimal('0.01'), rounding=ROUND_DOWN)
        return original, bundle_price

    def refresh_prices(self):
        original, bundle_price = self.calculate_prices()
        Product.objects.filter(pk=self.product_id).update(
            price=original,
            promo_price=bundle_price,
            promo_start=None,
            promo_end=None,
        )
        self.product.price=original
        self.product.promo_price=bundle_price
        self.product.promo_start=None
        self.product.promo_end=None


class BundleProduct(Product):
    class Meta:
        proxy=True
        verbose_name='bundle'
        verbose_name_plural='bundles'


class FreePDFProduct(Product):
    class Meta:
        proxy=True
        verbose_name='free PDF'
        verbose_name_plural='free PDFs'


class Author(models.Model):
    name = models.CharField(max_length=150)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Publisher(models.Model):
    name = models.CharField(max_length=150, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Book(models.Model):
    class Format(models.TextChoices):
        PAPERBACK = 'paperback', 'Paperback'
        HARDCOVER = 'hardcover', 'Hardcover'
        EBOOK = 'ebook', 'eBook'
        AUDIOBOOK = 'audiobook', 'Audiobook'

    product = models.OneToOneField(
        Product,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='book',
    )
    authors = models.ManyToManyField(Author, related_name='books')
    isbn = models.CharField(
        'ISBN',
        max_length=17,
        unique=True,
        validators=[RegexValidator(r'^[0-9Xx-]{10,17}$', 'Enter a valid ISBN-10 or ISBN-13 (digits and hyphens).')],
    )
    language = models.CharField(max_length=50)
    book_format = models.CharField('book format', max_length=20, choices=Format.choices)
    pages = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    publication_date = models.DateField('date published')
    publisher = models.ForeignKey(Publisher, on_delete=models.PROTECT, related_name='books')

    def __str__(self):
        return self.product.title


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['product', 'user'],
                name='review_one_per_user_per_product',
                violation_error_message='You have already reviewed this product.',
            ),
            models.CheckConstraint(
                condition=Q(rating__gte=1) & Q(rating__lte=5),
                name='review_rating_between_1_and_5',
                violation_error_message='Rating must be between 1 and 5.',
            ),
        ]

    def __str__(self):
        return f'{self.user} - {self.product} ({self.rating})'
