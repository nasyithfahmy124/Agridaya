from rest_framework import serializers
from .models import FarmerProfile, FarmIdentity
from .models import CultivationLog
from rest_framework import serializers

class FarmIdentitySerializer(serializers.ModelSerializer):
    class Meta:
        model = FarmIdentity
        fields = ["id", "nama_lahan", "luas_lahan", "tipe_tanah", "lokasi_daerah", "koordinat_dummy"]
        read_only_fields = ["id", "koordinat_dummy"]

class FarmerProfileSerializer(serializers.ModelSerializer):
    farm_identity = FarmIdentitySerializer() 

    class Meta:
        model = FarmerProfile
        fields = [
            "id", "nama_petani", "foto_profil", "tahun_pengalaman", 
            "komoditas_utama", "deskripsi_singkat", "farm_identity"
        ]
        read_only_fields = ["id"]
    def update(self, instance, validated_data):
        farm_data = validated_data.pop('farm_identity', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if farm_data and instance.farm_identity:
            farm_instance = instance.farm_identity
            for attr, value in farm_data.items():
                setattr(farm_instance, attr, value)
            farm_instance.koordinat_dummy = "-6.20, 106.84" if "jakarta" in farm_data.get('lokasi_daerah', '').lower() else "-7.25, 112.76"
            farm_instance.save()

        return instance

class FarmIdentityUpdateSerializer(serializers.Serializer):
    nama_petani = serializers.CharField(max_length=150)
    foto_profil = serializers.CharField(
        max_length=500, required=False, allow_blank=True, allow_null=True
    )
    tahun_pengalaman = serializers.IntegerField(min_value=0)
    komoditas_utama = serializers.CharField(
        max_length=200, required=False, allow_blank=True
    )
    deskripsi_singkat = serializers.CharField(required=False, allow_blank=True)

    nama_lahan = serializers.CharField(max_length=150)
    luas_lahan = serializers.DecimalField(max_digits=6, decimal_places=2)
    tipe_tanah = serializers.CharField(max_length=100)
    lokasi_daerah = serializers.CharField(max_length=150)
    

class CultivationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = CultivationLog
        fields = [
            "id",
            "farm_identity",
            "tanggal",
            "aktivitas",
            "input_digunakan",
            "catatan_lapangan",
            "dokumentasi"
        ]
        read_only_fields = ["id", "farm_identity"]