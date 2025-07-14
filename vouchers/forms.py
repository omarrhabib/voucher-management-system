# vouchers/forms.py

from django import forms
from .models import Voucher, Item
from django.forms import inlineformset_factory

class VoucherForm(forms.ModelForm):
    class Meta:
        model = Voucher
        fields = ['voucher_type']
        widgets = {
            'voucher_type': forms.RadioSelect,
        }

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['account', 'description', 'amount']

# This is the magic! It creates a set of forms for the items
# related to a single voucher.
ItemFormSet = inlineformset_factory(
    Voucher,
    Item,
    form=ItemForm,
    extra=1, # Start with one extra form
    can_delete=True, # Allow deletion of forms
    can_delete_extra=True,
)