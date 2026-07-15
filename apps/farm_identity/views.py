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
        

class CultivationLogListView(generics.ListCreateAPIView):
    serializer_class = CultivationLogSerializer
    permission_classes = [IsAuthenticated] 

    def get_queryset(self):
        if self.request.user.is_authenticated:
            try:
                user_profile = self.request.user.farmer
                user_farm = FarmIdentity.objects.filter(farmer=user_profile).first()
                if user_farm:
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
        self.perform_create(serializer)
        
        return Response(
            {
                "message": "Entri Log Budidaya baru berhasil disimpan ke database!",
                "data": serializer.data
            },
            status=status.HTTP_201_CREATED
        )

    def perform_create(self, serializer):
        user = self.request.user
        user_profile, created = FarmerProfile.objects.get_or_create(
            user=user,
            defaults={"nama_petani": user.username.capitalize()}
        )
        user_farm, created_farm = FarmIdentity.objects.get_or_create(
            farmer=user_profile, # Disesuaikan menjadi 'farmer' bukan 'farmer_profile'
            defaults={
                "nama_lahan": "Lahan Utama " + user_profile.nama_petani,
                "luas_lahan": "1.00",
                "tipe_tanah": "Tanah Lempung",
                "lokasi_daerah": "Indonesia"
            }
        )
        serializer.save(farm_identity=user_farm)