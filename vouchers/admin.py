# vouchers/admin.py
from django.contrib import admin
from .models import Voucher, BankPaymentVoucher, BankReceiptVoucher, Item

admin.site.register(Voucher)
admin.site.register(BankPaymentVoucher)
admin.site.register(BankReceiptVoucher)
admin.site.register(Item)