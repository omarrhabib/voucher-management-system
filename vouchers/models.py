# vouchers/models.py

from django.db import models
from django.db.models import Sum
from django.urls import reverse

class Voucher(models.Model):
    # Define choices for the voucher type
    VOUCHER_TYPE_CHOICES = [
        ('Payment', 'Payment'),
        ('Receipt', 'Receipt'),
    ]

    # Fields for the Voucher table
    # VoucherID is automatically created by Django as 'id' (AutoField, Primary Key)
    voucher_id = models.AutoField(primary_key=True)
    date = models.DateField(auto_now_add=True)
    voucher_type = models.CharField(max_length=10, choices=VOUCHER_TYPE_CHOICES)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Voucher #{self.voucher_id} - {self.date}"

    def get_absolute_url(self):
        # This will be used to redirect after creating a voucher
        return reverse('voucher_detail', args=[str(self.voucher_id)])

    def calculate_total(self):
        # Calculate total from related items
        total = self.items.aggregate(total=Sum('amount'))['total'] or 0.00
        return total

    def save(self, *args, **kwargs):
        # We override save to calculate total amount, but it's better to do this
        # in the view right before saving the instance to ensure data integrity.
        # However, for demonstration, we can leave a placeholder or implement it here.
        # The total amount will be calculated and set in the view logic.
        super().save(*args, **kwargs)


class Item(models.Model):
    # The composite primary key (VoucherID, Sr) is not idiomatic in Django.
    # A single AutoField 'id' is much simpler and more efficient.
    # We will generate the 'Sr' number during display (in the template).

    # Fields for the Item table
    voucher = models.ForeignKey(Voucher, related_name='items', on_delete=models.CASCADE)
    # Sr number will be handled in the template using forloop.counter
    account = models.CharField(max_length=100)
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2) # Use DecimalField for money

    def __str__(self):
        return f"Item for Voucher #{self.voucher.voucher_id} - {self.description}" 