# vouchers/forms.py
from django import forms
from .models import Voucher, Item, BankPaymentVoucher, BankReceiptVoucher

class VoucherForm(forms.ModelForm):
    # We add all possible fields here. We will show/hide them with JS.
    bank = forms.CharField(required=False)
    cheque_no = forms.CharField(required=False)
    inst_type = forms.CharField(required=False, label="Instrument Type")
    inst_no = forms.CharField(required=False, label="Instrument Number")
    
    class Meta:
        model = Voucher
        fields = ['date', 'payee', 'memo', 'prepared_by']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'memo': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add a custom class for styling mandatory fields
        for field_name in ['date', 'payee', 'prepared_by']:
            self.fields[field_name].widget.attrs.update({'class': 'mandatory-field'})

    def clean(self):
        cleaned_data = super().clean()
        # The view will pass voucher_type, we need to validate based on it
        voucher_type = self.data.get('voucher_type')
        
        if voucher_type in ['BPV', 'BRV']:
            if not cleaned_data.get('bank'):
                self.add_error('bank', 'This field is required for Bank Vouchers.')
        
        if voucher_type == 'BPV':
            if not cleaned_data.get('cheque_no'):
                self.add_error('cheque_no', 'This field is required for Bank Payment Vouchers.')

        if voucher_type == 'BRV':
            if not cleaned_data.get('inst_type'):
                self.add_error('inst_type', 'This field is required for Bank Receipt Vouchers.')
            if not cleaned_data.get('inst_no'):
                self.add_error('inst_no', 'This field is required for Bank Receipt Vouchers.')
        
        return cleaned_data

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['account', 'description', 'amount']

ItemFormSet = forms.inlineformset_factory(
    Voucher,
    Item,
    form=ItemForm,
    extra=1,
    can_delete=True,
    can_delete_extra=True
)