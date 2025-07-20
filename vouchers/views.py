# vouchers/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.db.models import F, Window
from django.db.models.functions import Lag, Lead
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML, CSS
from .models import Voucher, BankPaymentVoucher, BankReceiptVoucher, Item
from .forms import VoucherForm, ItemFormSet
from weasyprint import HTML, CSS # Make sure CSS is imported from weasyprint

def landing_page(request):
    return render(request, 'vouchers/landing_page.html')

def voucher_list(request):
    vouchers = Voucher.objects.all().order_by('-date', '-voucher_id')
    paginator = Paginator(vouchers, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'vouchers/voucher_list.html', {'page_obj': page_obj})

def create_voucher(request):
    if request.method == 'POST':
        voucher_form = VoucherForm(request.POST)
        item_formset = ItemFormSet(request.POST, prefix='items')
        voucher_type = request.POST.get('voucher_type')

        if voucher_form.is_valid() and item_formset.is_valid():
            with transaction.atomic():
                common_data = {
                    'date': voucher_form.cleaned_data['date'],
                    'payee': voucher_form.cleaned_data['payee'],
                    'memo': voucher_form.cleaned_data['memo'],
                    'prepared_by': voucher_form.cleaned_data['prepared_by'],
                }

                if voucher_type == 'BPV':
                    voucher = BankPaymentVoucher.objects.create(
                        **common_data,
                        bank=voucher_form.cleaned_data['bank'],
                        cheque_no=voucher_form.cleaned_data['cheque_no']
                    )
                elif voucher_type == 'BRV':
                    voucher = BankReceiptVoucher.objects.create(
                        **common_data,
                        bank=voucher_form.cleaned_data['bank'],
                        inst_type=voucher_form.cleaned_data['inst_type'],
                        inst_no=voucher_form.cleaned_data['inst_no']
                    )
                else: # CPV or CRV
                    voucher = Voucher.objects.create(
                        **common_data,
                        voucher_type=voucher_type
                    )
                
                item_formset.instance = voucher
                item_formset.save()
                
                # Recalculate total and save again to generate amount_in_words
                voucher.total_amount = voucher.calculate_total()
                voucher.save()

            return redirect(voucher.get_absolute_url())
    else:
        voucher_form = VoucherForm()
        item_formset = ItemFormSet(prefix='items', queryset=Item.objects.none())

    context = {
        'voucher_form': voucher_form,
        'item_formset': item_formset,
        'voucher_types': Voucher.VOUCHER_TYPE_CHOICES,
    }
    return render(request, 'vouchers/create_voucher.html', context)

# vouchers/views.py

def voucher_detail(request, voucher_id):
    # Get the main voucher object for display
    voucher_base = get_object_or_404(Voucher, pk=voucher_id)
    voucher = voucher_base.get_child_instance()

    # --- NEW NAVIGATION LOGIC THAT AVOIDS WINDOW FUNCTIONS ---

    # Find the next voucher
    next_voucher = Voucher.objects.filter(voucher_id__gt=voucher_id).order_by('voucher_id').first()

    # Find the previous voucher
    prev_voucher = Voucher.objects.filter(voucher_id__lt=voucher_id).order_by('-voucher_id').first()

    # --- END NEW LOGIC ---

    context = {
        'voucher': voucher,
        'next_id': next_voucher.voucher_id if next_voucher else None,
        'prev_id': prev_voucher.voucher_id if prev_voucher else None,
    }
    return render(request, 'vouchers/voucher_detail.html', context)
# vouchers/views.py
''' 2nd
def voucher_detail(request, voucher_id):
    # Step 1: Get the specific voucher object we are viewing. This is for the main display.
    voucher_base = get_object_or_404(Voucher, pk=voucher_id)
    voucher = voucher_base.get_child_instance()

    # --- CORRECTED NAVIGATION LOGIC ---

    # Step 2: Annotate the ENTIRE Voucher table to find the next/prev IDs for every row.
    # The `order_by` argument inside Lead/Lag defines the window's ordering.
    annotated_queryset = Voucher.objects.annotate(
        next_id=Lead('voucher_id', order_by=F('voucher_id').asc()),
        prev_id=Lag('voucher_id', order_by=F('voucher_id').asc())
    )

    # Step 3: Now that all rows are annotated, filter down to the specific one we need.
    nav_voucher = annotated_queryset.filter(pk=voucher_id).first()
    
    # --- END CORRECTION ---

    context = {
        'voucher': voucher,
        'next_id': nav_voucher.next_id if nav_voucher else None,
        'prev_id': nav_voucher.prev_id if nav_voucher else None,
    }
    return render(request, 'vouchers/voucher_detail.html', context)

    2nd 
    '''
# ---------------
'''
def voucher_detail(request, voucher_id):
    voucher_base = get_object_or_404(Voucher, pk=voucher_id)
    voucher = voucher_base.get_child_instance() # Get the specific child instance

    # Navigation logic for Next/Previous
    # window = Window(expression=F('voucher_id'), order_by=F('voucher_id').asc())
    window = Window(order_by=F('voucher_id').asc())
    nav_vouchers = Voucher.objects.annotate(
        next_id=Lead('voucher_id', over=window),
        prev_id=Lag('voucher_id', over=window)
    ).filter(pk=voucher_id).first()

    context = {
        'voucher': voucher,
        'next_id': nav_vouchers.next_id if nav_vouchers else None,
        'prev_id': nav_vouchers.prev_id if nav_vouchers else None,
    }
    return render(request, 'vouchers/voucher_detail.html', context)
'''



def download_voucher_pdf(request, voucher_id):
    """
    Generates a PDF from the dedicated, self-contained print template.
    """
    voucher_base = get_object_or_404(Voucher, pk=voucher_id)
    voucher = voucher_base.get_child_instance()

    # Render the DEDICATED print template
    html_string = render_to_string(
        'vouchers/voucher_print_template.html',
        {'voucher': voucher}
    )

    # Convert to PDF. The base_url is still crucial for finding the logo image.
    pdf_file = HTML(
        string=html_string,
        base_url=request.build_absolute_uri('/')
    ).write_pdf()

    # Create the HTTP response
    response = HttpResponse(pdf_file, content_type='application/pdf')
    filename = f"{voucher.voucher_id}_{voucher.date}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    return response


'''
x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x 


def download_voucher_pdf(request, voucher_id):
    """
    Generates a PDF from a self-contained HTML template.
    """
    voucher_base = get_object_or_404(Voucher, pk=voucher_id)
    voucher = voucher_base.get_child_instance()

    # The template 'voucher_pdf.html' now contains all necessary styles.
    html_string = render_to_string(
        'vouchers/voucher_pdf.html',
        {'voucher': voucher}
    )

    # Convert the HTML to PDF. The base_url is still crucial for finding the logo image.
    pdf_file = HTML(
        string=html_string,
        base_url=request.build_absolute_uri('/')
    ).write_pdf()

    # Create the HTTP response
    response = HttpResponse(pdf_file, content_type='application/pdf')
    filename = f"{voucher.voucher_id}_{voucher.date}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    return response
'''
    
'''
def download_voucher_pdf(request, voucher_id):
    voucher_base = get_object_or_404(Voucher, pk=voucher_id)
    voucher = voucher_base.get_child_instance()
    
    html_string = render_to_string('vouchers/voucher_pdf.html', {'voucher': voucher})
    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()
    
    response = HttpResponse(pdf_file, content_type='application/pdf')
    filename = f"{voucher.voucher_id}_{voucher.date}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
'''