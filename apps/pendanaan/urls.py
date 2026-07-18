from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ProjectViewSet,
    KebutuhanBarangViewSet,
    DonasiViewSet,
    DonasiBarangViewSet,
    LaporanViewSet,
    HasilPanenViewSet,
)

router = DefaultRouter()
router.register(r'form-dana', ProjectViewSet, basename='project')
router.register(r'kebutuhan-barang', KebutuhanBarangViewSet, basename='kebutuhanbarang')
router.register(r'donasi', DonasiViewSet, basename='donasi')
router.register(r'donasi-barang', DonasiBarangViewSet, basename='donasibarang')
router.register(r'laporan', LaporanViewSet, basename='laporan')
router.register(r'hasil-panen', HasilPanenViewSet, basename='hasilpanen')

urlpatterns = [
    path('', include(router.urls)),
]

# Daftarkan ini di urls.py utama project, contoh:
#
# urlpatterns = [
#     ...
#     path('api/pendanaan/', include('pendanaan.urls')),
# ]
#
# Endpoint yang tersedia (contoh):
#   GET/POST      /api/pendanaan/projects/
#   GET/PUT/PATCH/DELETE  /api/pendanaan/projects/{id}/
#   GET           /api/pendanaan/projects/{id}/riwayat-bantuan/
#   GET           /api/pendanaan/projects/{id}/bagi-hasil/
#
#   GET/POST      /api/pendanaan/donasi/
#   GET           /api/pendanaan/donasi/riwayat/?donatur_id=1
#   GET           /api/pendanaan/donasi/dashboard-bagi-hasil/?donatur_id=1
#
#   GET/POST      /api/pendanaan/donasi-barang/
#
#   GET/POST      /api/pendanaan/laporan/
#   GET           /api/pendanaan/laporan/by-project/{project_id}/
#
#   GET/POST      /api/pendanaan/hasil-panen/