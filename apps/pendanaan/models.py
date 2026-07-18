from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from apps.farm_identity.models import FarmIdentity


class Project(models.Model):
    STATUS_AKTIF = 'aktif'
    STATUS_SELESAI = 'selesai'
    STATUS_DIBATALKAN = 'dibatalkan'

    STATUS_CHOICES = [
        (STATUS_AKTIF, 'Aktif'),
        (STATUS_SELESAI, 'Selesai'),
        (STATUS_DIBATALKAN, 'Dibatalkan'),
    ]

    farm_identity = models.ForeignKey(
        FarmIdentity,
        on_delete=models.CASCADE,
        related_name='projects',
        help_text='Identitas lahan petani pemilik proyek ini.'
    )
    nama = models.CharField(max_length=150)
    deskripsi = models.TextField(blank=True)
    lokasi = models.CharField(max_length=150, blank=True)
    target_dana = models.DecimalField(
        max_digits=14, decimal_places=2, default=0,
        validators=[MinValueValidator(Decimal('0'))]
    )
    gambar = models.ImageField(upload_to='project/', blank=True, null=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_AKTIF
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return self.nama


class KebutuhanBarang(models.Model):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='kebutuhan_barang'
    )
    nama_barang = models.CharField(max_length=150)
    jumlah_dibutuhkan = models.PositiveIntegerField()
    satuan = models.CharField(max_length=50, default='item')
    harga_satuan = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    @property
    def total_harga(self):
        return self.jumlah_dibutuhkan * self.harga_satuan

    @property
    def jumlah_terpenuhi(self):
        agg = self.item_donasi.aggregate(total=models.Sum('jumlah'))
        return agg['total'] or 0

    def __str__(self):
        return f"{self.nama_barang} - {self.project.nama}"


class Donasi(models.Model):
    donatur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='donasi_uang'
    )
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='donasi_set'
    )
    jumlah = models.DecimalField(
        max_digits=14, decimal_places=2,
        validators=[MinValueValidator(Decimal('1'))]
    )
    catatan = models.CharField(max_length=255, blank=True)
    tanggal = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-tanggal']

    def __str__(self):
        return f"{self.donatur} -> {self.project} : Rp{self.jumlah}"


class DonasiBarang(models.Model):
    donatur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='donasi_barang'
    )
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='donasi_barang_set'
    )
    catatan = models.CharField(max_length=255, blank=True)
    tanggal = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-tanggal']
        verbose_name_plural = 'Donasi Barang'

    def __str__(self):
        return f"DonasiBarang #{self.pk} - {self.donatur}"


class DonasiBarangItem(models.Model):
    donasi = models.ForeignKey(
        DonasiBarang, on_delete=models.CASCADE, related_name='items'
    )
    kebutuhan = models.ForeignKey(
        KebutuhanBarang, on_delete=models.CASCADE, related_name='item_donasi'
    )
    jumlah = models.PositiveIntegerField()

    @property
    def nilai_rupiah(self):
        return self.jumlah * self.kebutuhan.harga_satuan

    def __str__(self):
        return f"{self.jumlah} x {self.kebutuhan.nama_barang}"


class Laporan(models.Model):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='laporan'
    )
    judul = models.CharField(max_length=150, blank=True)
    deskripsi = models.TextField(blank=True)
    jumlah_pengeluaran = models.DecimalField(
        max_digits=14, decimal_places=2, default=0
    )
    bukti = models.FileField(upload_to='laporan/', blank=True, null=True)
    tanggal = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-tanggal']

    def __str__(self):
        return f"Laporan {self.project.nama} - {self.tanggal:%Y-%m-%d}"


class HasilPanen(models.Model):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='hasil_panen'
    )
    total_pendapatan = models.DecimalField(
        max_digits=14, decimal_places=2, default=0
    )
    keterangan = models.TextField(blank=True)
    bukti = models.FileField(upload_to='hasil_panen/', blank=True, null=True)
    tanggal = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-tanggal']
        verbose_name_plural = 'Hasil Panen'

    def __str__(self):
        return f"Hasil Panen {self.project.nama} - {self.tanggal:%Y-%m-%d}"