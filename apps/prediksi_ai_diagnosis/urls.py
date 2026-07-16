from django.urls import path,include
from . import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'prediksi-panen',views.AktivitasView,basename='prediksi')
diagnosis = DefaultRouter()
diagnosis.register(f'diagnosis-penyakit',views.AIDiagnosisViewSet,basename='diagnosis')
urlpatterns = [
    path('',include(router.urls)),
    path('',include(diagnosis.urls))
]
