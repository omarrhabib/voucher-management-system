# vouchers/models.py
from django.db import models, transaction
from django.urls import reverse
from django.utils import timezone
from num2words import num2words

# --- The Parent Model for ALL Vouchers ---
class Voucher(models.Model):
    VOUCHER_TYPE_CHOICES = [
        ('BPV', 'Bank Payment'),
        ('BRV', 'Bank Receipt'),
        ('CPV', 'Cash Payment'),
        ('CRV', 'Cash Receipt'),
    ]
    
    # Custom Primary Key
    voucher_id = models.CharField(max_length=15, primary_key=True, unique=True, editable=False)
    
    # Common Fields
    voucher_type = models.CharField(max_length=3, choices=VOUCHER_TYPE_CHOICES)
    date = models.DateField(default=timezone.now)
    payee = models.CharField(max_length=255)
    memo = models.TextField(blank=True, null=True)
    prepared_by = models.CharField(max_length=100)
    
    # Auto-calculated Fields
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    amount_in_words = models.CharField(max_length=255, blank=True, editable=False)

    def get_child_instance(self):
        """Returns the actual child instance (e.g., BankPaymentVoucher)"""
        if self.voucher_type == 'BPV':
            return self.bankpaymentvoucher
        if self.voucher_type == 'BRV':
            return self.bankreceiptvoucher
        return self # For CPV and CRV

    def get_voucher_type_display_full(self):
        """Returns the full name like 'Bank Payment Voucher'"""
        return f"{self.get_voucher_type_display()} Voucher"

    def get_absolute_url(self):
        return reverse('voucher_detail', args=[str(self.voucher_id)])

    def calculate_total(self):
        total = self.items.aggregate(total=models.Sum('amount'))['total'] or 0.00
        return total

    def save(self, *args, **kwargs):
        # Generate custom Voucher ID on first save
        if not self.voucher_id:
            with transaction.atomic():
                last_voucher = Voucher.objects.filter(voucher_type=self.voucher_type).order_by('voucher_id').last()
                if last_voucher:
                    last_number = int(last_voucher.voucher_id.split('-')[-1])
                    new_number = last_number + 1
                else:
                    new_number = 1
                self.voucher_id = f"{self.voucher_type}-{new_number:05d}"

        # Calculate total amount and amount in words
        # Note: This is best done *after* items are saved. We'll call save() again from the view.
        if self.total_amount > 0:
            rupees = int(self.total_amount)
            paisas = int((self.total_amount - rupees) * 100)
            words = f"{num2words(rupees, lang='en_IN').title()} Rupees"
            if paisas > 0:
                words += f" and {num2words(paisas, lang='en_IN').title()} Paisas"
            else:
                words += " only"
            self.amount_in_words = words

        super().save(*args, **kwargs)

    def __str__(self):
        return self.voucher_id

# --- Child Model for Bank Payment ---
class BankPaymentVoucher(Voucher):
    bank = models.CharField(max_length=100)
    cheque_no = models.CharField(max_length=50)
    
    def save(self, *args, **kwargs):
        self.voucher_type = 'BPV'
        super().save(*args, **kwargs)

# --- Child Model for Bank Receipt ---
class BankReceiptVoucher(Voucher):
    bank = models.CharField(max_length=100)
    inst_type = models.CharField("Instrument Type", max_length=50)
    inst_no = models.CharField("Instrument Number", max_length=50)

    def save(self, *args, **kwargs):
        self.voucher_type = 'BRV'
        super().save(*args, **kwargs)

# --- Item Model (Unchanged as requested, but linking to new Voucher model) ---
class Item(models.Model):
    voucher = models.ForeignKey(Voucher, related_name='items', on_delete=models.CASCADE)
    account = models.CharField(max_length=100)
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Item for {self.voucher.voucher_id} - {self.description}"