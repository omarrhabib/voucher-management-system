# vouchers/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_page, name='landing_page'),
    path('vouchers/', views.voucher_list, name='voucher_list'),
    path('new-voucher/', views.create_voucher, name='create_voucher'),
    # Use <str:voucher_id> because our pk is now a string
    path('vouchers/<str:voucher_id>/', views.voucher_detail, name='voucher_detail'),
    path('vouchers/<str:voucher_id>/download/', views.download_voucher_pdf, name='download_voucher_pdf'),
]