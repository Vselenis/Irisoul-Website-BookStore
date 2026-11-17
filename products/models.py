from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models
from django.db.models import F, Q
from django.urls import reverse

# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=100,unique=True)
    slug = models.SlugField(max_length=120,unique=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name


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
    image = models.ImageField(upload_to='products/')
    categories = models.ManyToManyField(Category, related_name='products')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

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
        ]

    def __str__(self):
        return self.title


    def get_absolute_url(self):
        return reverse(f'products:{self.product_type}-detail', kwargs={'slug': self.slug})

    def clean(self):
        super().clean()
        if self.promo_price is not None and self.price is not None and self.promo_price >= self.price:
            raise ValidationError({'promo_price': 'Promo price must be lower than the regular price.'})

    @property
    def has_promo(self):
        return self.promo_price is not None

    @property
    def current_price(self):
        return self.promo_price if self.has_promo else self.price

    @property
    def discount_percent(self):
        if not self.has_promo or not self.price:
            return 0
        return round((self.price - self.promo_price) / self.price * 100)


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
