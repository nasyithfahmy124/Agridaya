from decimal import Decimal

from django.db import transaction
from django.db.models import Sum, F
from django.db.models.functions import Coalesce
from rest_framework import serializers

from .models import (
    Project,
    KebutuhanBarang,
    Donasi,
    DonasiBarang,
    DonasiBarangItem,
    Laporan,
    HasilPanen,
)


class KebutuhanBarangSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    jumlah_terpenuhi = serializers.ReadOnlyField()
    total_harga = serializers.ReadOnlyField()

    class Meta:
        model = KebutuhanBarang
        fields = [
            'id', 'nama_barang', 'jumlah_dibutuhkan',
            'satuan', 'harga_satuan', 'total_harga', 'jumlah_terpenuhi',
        ]


class ProjectSerializer(serializers.ModelSerializer):
    kebutuhan_barang = KebutuhanBarangSerializer(many=True, required=False)

    total_donasi_uang = serializers.SerializerMethodField()
    sisa_target_dana = serializers.SerializerMethodField()
    total_barang_masuk = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            'id', 'farm_identity', 'nama', 'deskripsi', 'lokasi',
            'target_dana', 'gambar', 'status',
            'kebutuhan_barang',
            'total_donasi_uang', 'sisa_target_dana', 'total_barang_masuk',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['status', 'created_at', 'updated_at']

    def get_total_donasi_uang(self, obj):
        return obj.donasi_set.aggregate(
            total=Coalesce(Sum('jumlah'), Decimal('0'))
        )['total']

    def get_sisa_target_dana(self, obj):
        total = self.get_total_donasi_uang(obj)
        sisa = obj.target_dana - total
        return sisa if sisa > 0 else Decimal('0')

    def get_total_barang_masuk(self, obj):
        return DonasiBarangItem.objects.filter(
            kebutuhan__project=obj
        ).aggregate(
            total=Coalesce(Sum(F('jumlah') * F('kebutuhan__harga_satuan')), Decimal('0'))
        )['total']

    @transaction.atomic
    def create(self, validated_data):
        kebutuhan_data = validated_data.pop('kebutuhan_barang', [])
        project = Project.objects.create(**validated_data)

        for item in kebutuhan_data:
            item.pop('id', None)
            KebutuhanBarang.objects.create(project=project, **item)

        return project

    @transaction.atomic
    def update(self, instance, validated_data):
        kebutuhan_data = validated_data.pop('kebutuhan_barang', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if kebutuhan_data is not None:
            existing_ids = list(
                instance.kebutuhan_barang.values_list('id', flat=True)
            )
            sent_ids = []

            for item in kebutuhan_data:
                item_id = item.pop('id', None)
                if item_id and item_id in existing_ids:
                    KebutuhanBarang.objects.filter(id=item_id).update(**item)
                    sent_ids.append(item_id)
                else:
                    new_obj = KebutuhanBarang.objects.create(
                        project=instance, **item
                    )
                    sent_ids.append(new_obj.id)
            instance.kebutuhan_barang.exclude(id__in=sent_ids).delete()

        return instance

class DonasiSerializer(serializers.ModelSerializer):
    class Meta:
        model = Donasi
        fields = ['id', 'donatur', 'project', 'jumlah', 'catatan', 'tanggal']
        read_only_fields = ['tanggal']

    def validate(self, attrs):
        project = attrs.get('project') or getattr(self.instance, 'project', None)
        jumlah = attrs.get('jumlah') or getattr(self.instance, 'jumlah', None)

        if project.status != Project.STATUS_AKTIF:
            raise serializers.ValidationError(
                'Project ini sudah tidak menerima donasi (status bukan aktif).'
            )

        total_terkumpul = Donasi.objects.filter(project=project).aggregate(
            total=Coalesce(Sum('jumlah'), Decimal('0'))
        )['total']

        sisa = project.target_dana - total_terkumpul

        if jumlah > sisa:
            raise serializers.ValidationError(
                {'jumlah': f'Melebihi sisa target dana. Maksimal donasi saat ini: {sisa}'}
            )

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        donasi = Donasi.objects.create(**validated_data)

        project = donasi.project
        total_baru = Donasi.objects.filter(project=project).aggregate(
            total=Coalesce(Sum('jumlah'), Decimal('0'))
        )['total']

        if total_baru >= project.target_dana:
            project.status = Project.STATUS_SELESAI
            project.save(update_fields=['status'])

        return donasi

class DonasiBarangItemSerializer(serializers.ModelSerializer):
    nama_barang = serializers.CharField(
        source='kebutuhan.nama_barang', read_only=True
    )
    nilai_rupiah = serializers.ReadOnlyField()

    class Meta:
        model = DonasiBarangItem
        fields = ['id', 'kebutuhan', 'nama_barang', 'jumlah', 'nilai_rupiah']


class DonasiBarangSerializer(serializers.ModelSerializer):
    items = DonasiBarangItemSerializer(many=True)

    class Meta:
        model = DonasiBarang
        fields = ['id', 'donatur', 'project', 'catatan', 'tanggal', 'items']
        read_only_fields = ['tanggal']

    def validate_items(self, items):
        if not items:
            raise serializers.ValidationError(
                'Minimal harus ada 1 item barang yang didonasikan.'
            )
        return items

    def validate(self, attrs):
        project = attrs.get('project')
        items = attrs.get('items', [])

        for item in items:
            kebutuhan = item['kebutuhan']
            if kebutuhan.project_id != project.id:
                raise serializers.ValidationError(
                    f"Kebutuhan barang '{kebutuhan.nama_barang}' bukan milik project ini."
                )

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        donasi_barang = DonasiBarang.objects.create(**validated_data)

        for item in items_data:
            DonasiBarangItem.objects.create(donasi=donasi_barang, **item)

        return donasi_barang


class LaporanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Laporan
        fields = [
            'id', 'project', 'judul', 'deskripsi',
            'jumlah_pengeluaran', 'bukti', 'tanggal',
        ]
        read_only_fields = ['tanggal']

class HasilPanenSerializer(serializers.ModelSerializer):
    class Meta:
        model = HasilPanen
        fields = [
            'id', 'project', 'total_pendapatan',
            'keterangan', 'bukti', 'tanggal',
        ]
        read_only_fields = ['tanggal']


class BagiHasilSerializer(serializers.Serializer):
    project_id = serializers.IntegerField()
    project_nama = serializers.CharField()
    total_pendapatan = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_pengeluaran = serializers.DecimalField(max_digits=14, decimal_places=2)
    keuntungan_bersih = serializers.DecimalField(max_digits=14, decimal_places=2)
    keuntungan_petani = serializers.DecimalField(max_digits=14, decimal_places=2)
    keuntungan_donatur = serializers.DecimalField(max_digits=14, decimal_places=2)