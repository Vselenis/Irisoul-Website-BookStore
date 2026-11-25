from django import forms

from .models import MAX_QUANTITY

QUANTITY_ERROR = f'Quantity must be a whole number from 1 to {MAX_QUANTITY}.'


class QuantityForm(forms.Form):
    quantity = forms.IntegerField(
        min_value=1,
        max_value=MAX_QUANTITY,
        error_messages={key: QUANTITY_ERROR for key in ('required','invalid','min_value','max_value')},
    )
