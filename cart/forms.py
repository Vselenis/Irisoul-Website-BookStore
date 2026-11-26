from django import forms
from django.utils import timezone

from accounts.models import EU_COUNTRIES

CARD_FIELDS = ('card_number', 'card_expiry_month', 'card_expiry_year', 'card_name', 'card_cvc')


def text_input(placeholder, **attrs):
    return forms.TextInput(attrs={'class': 'form-control', 'placeholder': placeholder, **attrs})


def select(**attrs):
    return forms.Select(attrs={'class': 'form-control default-select', **attrs})


class CheckoutForm(forms.Form):
    PAYMENT_CASH = 'cash'
    PAYMENT_CARD = 'card'
    PAYMENT_CHOICES = [(PAYMENT_CASH, 'Cash on Delivery'),(PAYMENT_CARD, 'Credit Card Payment')]


    first_name = forms.CharField(label='First name',max_length=150, widget=text_input('First name *',autocomplete='given-name'))
    last_name = forms.CharField(label='Last name',max_length=150, widget=text_input('Last name *',autocomplete='family-name'))
    address = forms.CharField(label='Address',max_length=255, widget=text_input('Address *',autocomplete='address-line1'))
    apartment = forms.CharField(label='Apartment',max_length=100, required=False, widget=text_input('Apartment',autocomplete='address-line2'))
    country = forms.ChoiceField(label='Country', choices=[('', 'Country *')] + EU_COUNTRIES, widget=select(autocomplete='country'))
    city = forms.CharField(label='City / Town',max_length=100, widget=text_input('City / Town *',autocomplete='address-level2'))
    postcode = forms.CharField(label='Postcode',max_length=20, widget=text_input('Postcode *',autocomplete='postal-code'))
    phone = forms.CharField(label='Phone',max_length=20, widget=text_input('Phone *',autocomplete='tel'))
    company = forms.CharField(label='Company Name',max_length=100, required=False, widget=text_input('Company Name',autocomplete='organization'))
    email = forms.EmailField(label='Email', required=False, widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email', 'autocomplete': 'email'}))
    notes = forms.CharField(
        label='Additional information',
        max_length=1000,
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Additional information about the order or delivery'}),
    )
    payment_method = forms.ChoiceField(
        label='Payment Method',
        choices=PAYMENT_CHOICES,
        initial=PAYMENT_CASH,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
    )
    card_number = forms.CharField(label='Card number',max_length=30, required=False, widget=text_input('Card number *',autocomplete='cc-number', inputmode='numeric'))
    card_expiry_month = forms.ChoiceField(
        label='Expiry month',
        required=False,
        choices=[('', 'Month *')] + [(f'{month:02d}', f'{month:02d}') for month in range(1, 13)],
        widget=select(autocomplete='cc-exp-month'),
    )
    card_expiry_year = forms.ChoiceField(label='Expiry year', required=False, widget=select(autocomplete='cc-exp-year'))
    card_name = forms.CharField(label='Name on card',max_length=100, required=False, widget=text_input('Name on card *',autocomplete='cc-name'))
    card_cvc = forms.CharField(label='Card security code',max_length=10, required=False, widget=text_input('Card security code *',autocomplete='cc-csc', inputmode='numeric'))


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        year = timezone.now().year
        self.fields['card_expiry_year'].choices = [('', 'Year *')] + [(str(value), str(value)) for value in range(year, year + 11)]


    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('payment_method') == self.PAYMENT_CARD:
            for name in CARD_FIELDS:
                if not cleaned_data.get(name):
                    self.add_error(name, 'This field is required.')
        return cleaned_data
