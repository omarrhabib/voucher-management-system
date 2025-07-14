# vouchers/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.core.paginator import Paginator
from django.urls import reverse_lazy
from .models import Voucher, Item
from .forms import VoucherForm, ItemFormSet
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML

def voucher_list(request):
    """Displays the list of the last 10 vouchers with pagination."""
    voucher_list = Voucher.objects.all().order_by('-date', '-voucher_id')
    paginator = Paginator(voucher_list, 10) # Show 10 vouchers per page

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'vouchers/voucher_list.html', {'page_obj': page_obj})


def create_voucher(request):
    """Handles the creation of a new voucher with its items."""
    if request.method == 'POST':
        voucher_form = VoucherForm(request.POST)
        item_formset = ItemFormSet(request.POST, prefix='items')

        if voucher_form.is_valid() and item_formset.is_valid():
            with transaction.atomic(): # Ensure all or nothing database operations
                voucher = voucher_form.save(commit=False)
                voucher.total_amount = 0  # Initialize total amount
                voucher.save() # Save the voucher to get a voucher_id

                items = item_formset.save(commit=False)
                total_amount = 0
                for item in items:
                    item.voucher = voucher
                    item.save()
                    total_amount += item.amount
                
                # Update voucher with the calculated total amount
                voucher.total_amount = total_amount
                voucher.save()

            return redirect(voucher.get_absolute_url())

    else:
        voucher_form = VoucherForm()
        item_formset = ItemFormSet(prefix='items', queryset=Item.objects.none())

    context = {
        'voucher_form': voucher_form,
        'item_formset': item_formset,
    }
    return render(request, 'vouchers/create_voucher.html', context)


def voucher_detail(request, voucher_id):
    """Displays a single voucher and its items."""
    voucher = get_object_or_404(Voucher, voucher_id=voucher_id)
    return render(request, 'vouchers/voucher_detail.html', {'voucher': voucher})


# For PDF Generation (See Step 7)
# Add these imports at the top of vouchers/views.py

def download_voucher_pdf(request, voucher_id):
    """Generates and serves a PDF for a given voucher."""
    voucher = get_object_or_404(Voucher, voucher_id=voucher_id)
    
    # Render template
    html_string = render_to_string('vouchers/voucher_pdf.html', {'voucher': voucher})
    
    # Create PDF
    pdf = HTML(string=html_string).write_pdf()
    
    # Create response
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="voucher_{voucher_id}.pdf"'
    
    return response