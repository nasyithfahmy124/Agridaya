from django.urls import path
from . import views
urlpatterns = [
    path('marketplace/',views.CreateProduk().as_view(),name='buatproduk'),
    path('order/',views.OrderView.as_view(),name='order')
]
