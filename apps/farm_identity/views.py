from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated # Tambahan pengaman login

from .models import FarmerProfile, FarmIdentity, PLACEHOLDER_KOORDINAT, CultivationLog
from .serializers import (
    FarmerProfileSerializer, 
    FarmIdentityUpdateSerializer, 
    CultivationLogSerializer
)

MOCK_FARM_IDENTITY_DATA = {
    "id": None,
    "nama_petani": "Budi Santoso",
    "foto_profil": "https://placehold.co/200x200?text=Budi+Santoso",
    "tahun_pengalaman": 15,
    "komoditas_utama": "Padi, Jagung",
    "deskripsi_singkat": (
        "Petani berpengalaman yang fokus pada pengelolaan lahan padi dan "
        "jagung secara berkelanjutan di wilayah Jawa Timur."
    ),
    "farm_identity": {
        "id": None,
        "nama_lahan": "Green Valley Estate",
        "luas_lahan": "2.50",
        "tipe_tanah": "Lempung Berliat",
        "lokasi_daerah": "Surabaya, Jawa Timur",
        "koordinat_dummy": "-7.25, 112.76",
    },
}

class FarmIdentityView(generics.GenericAPIView):
    serializer_class = FarmIdentityUpdateSerializer

    def get(self, request):
        profile = FarmerProfile.objects.select_related("farm_identity").first()

        if profile is None:
            return Response(MOCK_FARM_IDENTITY_DATA, status=status.HTTP_200_OK)

        serializer = FarmerProfileSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        return self._handle_update(request)

    def put(self, request):
        return self._handle_update(request)

    def _handle_update(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        response_payload = {
            "id": 1,
            "nama_petani": data["nama_petani"],
            "foto_profil": data.get("foto_profil") or MOCK_FARM_IDENTITY_DATA["foto_profil"],
            "tahun_pengalaman": data["tahun_pengalaman"],
            "komoditas_utama": data.get("komoditas_utama", ""),
            "deskripsi_singkat": data.get("deskripsi_singkat", ""),
            "farm_identity": {
                "id": 1,
                "nama_lahan": data["nama_lahan"],
                "luas_lahan": str(data["luas_lahan"]),
                "tipe_tanah": data["tipe_tanah"],
                "lokasi_daerah": data["lokasi_daerah"],
                "koordinat_dummy": PLACEHOLDER_KOORDINAT,
            },
        }

        return Response(
            {
                "message": "Identitas lahan & profil petani berhasil diperbarui (simulasi).",
                "data": response_payload,
            },
            status=status.HTTP_200_OK,
        )
        

# ==================== LOG BUDIDAYA ====================
class CultivationLogListView(generics.ListCreateAPIView):
    serializer_class = CultivationLogSerializer
    # Pastikan user harus login terlebih dahulu agar request.user tidak bernilai AnonymousUser
    permission_classes = [IsAuthenticated] 

    def get_queryset(self):
        # Opsional: Hanya tampilkan log budidaya milik user yang sedang aktif login
        if self.request.user.is_authenticated:
            try:
                user_farm = self.request.user.farmer_profile.farm_identity
                return CultivationLog.objects.filter(farm_identity=user_farm)
            except AttributeError:
                return CultivationLog.objects.none()
        return CultivationLog.objects.all()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Di sini method perform_create dipanggil oleh Django REST Framework
        self.perform_create(serializer)
        
        return Response(
            {
                "message": "Entri Log Budidaya baru berhasil disimpan ke database!",
                "data": serializer.data
            },
            status=status.HTTP_201_CREATED
        )

    # 💡 TARUH METHOD INI DI SINI 💡
    def perform_create(self, serializer):
        # Ambil profil dari user yang sedang login secara otomatis
        user_profile = self.request.user.farmer_profile
        # Ambil lahan milik user tersebut
        user_farm = user_profile.farm_identity
        
        # Simpan log budidaya langsung dikaitkan ke lahan milik user tersebut
        serializer.save(farm_identity=user_farm)