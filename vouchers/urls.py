# vouchers/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.voucher_list, name='voucher_list'),
    path('create/', views.create_voucher, name='create_voucher'),
    path('<int:voucher_id>/', views.voucher_detail, name='voucher_detail'),
    path('<int:voucher_id>/download/', views.download_voucher_pdf, name='download_voucher_pdf'),
]