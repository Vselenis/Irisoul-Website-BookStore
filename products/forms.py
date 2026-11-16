from django import forms


class ProductFilterForm(forms.Form):
    SORT_CHOICES = [
        ('newest', 'Newest'),
        ('price_asc', 'Price: Low to High'),
        ('price_desc', 'Price: High to Low'),
        ('top_rated', 'Top Rated'),
    ]

    category = forms.MultipleChoiceField(required=False)
    min_price = forms.DecimalField(required=False, min_value=0, max_digits=10, decimal_places=2)
    max_price = forms.DecimalField(required=False, min_value=0, max_digits=10, decimal_places=2)
    min_rating = forms.DecimalField(required=False, min_value=0, max_value=5, max_digits=3, decimal_places=2)
    max_rating = forms.DecimalField(required=False, min_value=0, max_value=5, max_digits=3, decimal_places=2)
    promo = forms.BooleanField(required=False)
    sort = forms.ChoiceField(choices=SORT_CHOICES, required=False)

    def __init__(self, *args, categories=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].choices = [(category.slug, category.name) for category in categories]
