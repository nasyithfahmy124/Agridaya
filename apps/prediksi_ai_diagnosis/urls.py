from django.urls import path,include
from . import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'prediksi-panen',views.AktivitasView,basename='prediksi')

urlpatterns = [
    path('',include(router.urls))
]
