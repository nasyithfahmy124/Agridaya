from decimal import Decimal
from itertools import chain

from django.db import transaction
from django.db.models import Sum, F
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import (
    Project,
    KebutuhanBarang,
    Donasi,
    DonasiBarang,
    DonasiBarangItem,
    Laporan,
    HasilPanen,
)
from .serializers import (
    ProjectSerializer,
    KebutuhanBarangSerializer,
    DonasiSerializer,
    DonasiBarangSerializer,
    LaporanSerializer,
    HasilPanenSerializer,
    BagiHasilSerializer,
)



class ProjectViewSet(viewsets.ModelViewSet):

    queryset = Project.objects.select_related('farm_identity').prefetch_related(
        'kebutuhan_barang'
    )
    serializer_class = ProjectSerializer
    permission_classes = [AllowAny]

    @action(detail=True, methods=['get'], url_path='riwayat-bantuan')
    def riwayat_bantuan(self, request, pk=None):
    
        project = self.get_object()

        donasi_uang = Donasi.objects.filter(project=project).select_related('donatur')
        donasi_barang = DonasiBarang.objects.filter(project=project).select_related(
            'donatur'
        ).prefetch_related('items__kebutuhan')

        data = {
            'project': ProjectSerializer(project, context={'request': request}).data,
            'donasi_uang': DonasiSerializer(donasi_uang, many=True).data,
            'donasi_barang': DonasiBarangSerializer(donasi_barang, many=True).data,
        }
        return Response(data)

    @action(detail=True, methods=['get'], url_path='bagi-hasil')
    def bagi_hasil(self, request, pk=None):
        project = self.get_object()

        total_pendapatan = HasilPanen.objects.filter(project=project).aggregate(
            total=Coalesce(Sum('total_pendapatan'), Decimal('0'))
        )['total']

        total_pengeluaran = Laporan.objects.filter(project=project).aggregate(
            total=Coalesce(Sum('jumlah_pengeluaran'), Decimal('0'))
        )['total']

        keuntungan_bersih = total_pendapatan - total_pengeluaran
        keuntungan_petani = keuntungan_bersih * Decimal('0.6')
        keuntungan_donatur = keuntungan_bersih * Decimal('0.4')

        result = {
            'project_id': project.id,
            'project_nama': project.nama,
            'total_pendapatan': total_pendapatan,
            'total_pengeluaran': total_pengeluaran,
            'keuntungan_bersih': keuntungan_bersih,
            'keuntungan_petani': keuntungan_petani,
            'keuntungan_donatur': keuntungan_donatur,
        }
        serializer = BagiHasilSerializer(result)
        return Response(serializer.data)


class KebutuhanBarangViewSet(viewsets.ModelViewSet):
    queryset = KebutuhanBarang.objects.select_related('project')
    serializer_class = KebutuhanBarangSerializer
    permission_classes = [AllowAny]


class DonasiViewSet(viewsets.ModelViewSet):

    queryset = Donasi.objects.select_related('donatur', 'project')
    serializer_class = DonasiSerializer
    permission_classes = [AllowAny]

    @transaction.atomic
    def perform_create(self, serializer):
        serializer.save()

    @action(detail=False, methods=['get'], url_path='riwayat')
    def riwayat(self, request):
        donatur_id = request.query_params.get('donatur_id')
        if not donatur_id:
            return Response(
                {'detail': 'Parameter donatur_id wajib diisi.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        riwayat_uang = Donasi.objects.filter(donatur_id=donatur_id).select_related('project')
        riwayat_barang = DonasiBarang.objects.filter(
            donatur_id=donatur_id
        ).select_related('project').prefetch_related('items__kebutuhan')

        uang_data = DonasiSerializer(riwayat_uang, many=True).data
        for d in uang_data:
            d['tipe'] = 'uang'

        barang_data = DonasiBarangSerializer(riwayat_barang, many=True).data
        for d in barang_data:
            d['tipe'] = 'barang'

        gabungan = sorted(
            chain(uang_data, barang_data),
            key=lambda x: x['tanggal'],
            reverse=True,
        )
        return Response(gabungan)

    @action(detail=False, methods=['get'], url_path='dashboard-bagi-hasil')
    def dashboard_bagi_hasil(self, request):
        donatur_id = request.query_params.get('donatur_id')
        if not donatur_id:
            return Response(
                {'detail': 'Parameter donatur_id wajib diisi.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        total_uang = Donasi.objects.filter(donatur_id=donatur_id).aggregate(
            total=Coalesce(Sum('jumlah'), Decimal('0'))
        )['total']

        total_barang = DonasiBarangItem.objects.filter(
            donasi__donatur_id=donatur_id
        ).aggregate(
            total=Coalesce(Sum(F('jumlah') * F('kebutuhan__harga_satuan')), Decimal('0'))
        )['total']

        total_saldo = total_uang + total_barang

        petani_uang = Donasi.objects.filter(
            donatur_id=donatur_id
        ).values_list('project__farm_identity__farmer_id', flat=True)

        petani_barang = DonasiBarang.objects.filter(
            donatur_id=donatur_id
        ).values_list('project__farm_identity__farmer_id', flat=True)

        jumlah_petani = len(set(list(petani_uang) + list(petani_barang)))

        return Response({
            'total_uang': total_uang,
            'nilai_barang': total_barang,
            'total_saldo': total_saldo,
            'jumlah_petani_dibantu': jumlah_petani,
        })


class DonasiBarangViewSet(viewsets.ModelViewSet):
    queryset = DonasiBarang.objects.select_related('donatur', 'project').prefetch_related(
        'items__kebutuhan'
    )
    serializer_class = DonasiBarangSerializer
    permission_classes = [AllowAny]

    @transaction.atomic
    def perform_create(self, serializer):
        serializer.save()


class LaporanViewSet(viewsets.ModelViewSet):
    queryset = Laporan.objects.select_related('project')
    serializer_class = LaporanSerializer
    permission_classes = [AllowAny]

    @action(detail=False, methods=['get'], url_path='by-project/(?P<project_id>[^/.]+)')
    def by_project(self, request, project_id=None):
        laporan = self.get_queryset().filter(project_id=project_id)
        serializer = self.get_serializer(laporan, many=True)
        return Response(serializer.data)


class HasilPanenViewSet(viewsets.ModelViewSet):
    queryset = HasilPanen.objects.select_related('project')
    serializer_class = HasilPanenSerializer
    permission_classes = [AllowAny]

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        hasil_panen = serializer.save()

        project = hasil_panen.project
        total_pendapatan = HasilPanen.objects.filter(project=project).aggregate(
            total=Coalesce(Sum('total_pendapatan'), Decimal('0'))
        )['total']
        total_pengeluaran = Laporan.objects.filter(project=project).aggregate(
            total=Coalesce(Sum('jumlah_pengeluaran'), Decimal('0'))
        )['total']
        keuntungan_bersih = total_pendapatan - total_pengeluaran

        response_data = serializer.data
        response_data['bagi_hasil'] = {
            'total_pendapatan': total_pendapatan,
            'total_pengeluaran': total_pengeluaran,
            'keuntungan_bersih': keuntungan_bersih,
            'keuntungan_petani': keuntungan_bersih * Decimal('0.6'),
            'keuntungan_donatur': keuntungan_bersih * Decimal('0.4'),
        }
        headers = self.get_success_headers(serializer.data)
        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)