from django.db import models
from django.core.exceptions import ValidationError
from decimal import Decimal
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User

class Profil(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profil')
    level = models.CharField(max_length=50, default="Agripreneur Level 1")
    total_panen_musim = models.IntegerField(default=0, help_text="Total musim panen yang sudah dilalui")
    ekspor_berhasil = models.IntegerField(default=0, help_text="Jumlah ekspor yang sukses")
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    lokasi_asal = models.CharField(max_length=100, default="Semarang, Jawa Tengah")
    def __str__(self):
        return f"Profile - {self.user.username}"
    
class Lahan(models.Model):
    profile = models.ForeignKey(Profil, on_delete=models.CASCADE, related_name='lahan_set')
    nama_lahan = models.CharField(max_length=100, help_text="Contoh: Lahan Blok A, Lahan Sektor Utara")
    luas_lahan = models.FloatField(help_text="Luas lahan dalam satuan Hektar (Ha)")
    komoditas = models.CharField(max_length=100, default="Padi / Beras")
    lokasi = models.CharField(max_length=150,default="Semarang, Indonesia")
    # provinsi = models.CharField(max_length=100, default="Jawa Tengah")
    # kabupaten_kota = models.CharField(max_length=100, help_text="Contoh: Kabupaten Demak")
    # kecamatan = models.CharField(max_length=100, null=True, blank=True)
    STATUS_PILIHAN = [
        ('SEHAT', 'Sehat'),
        ('WASPADA', 'Waspada'),
        ('TERSERANG', 'Terserang Hama/Penyakit'),
    ]
    status_lahan = models.CharField(max_length=20, choices=STATUS_PILIHAN, default='SEHAT')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class MusimTanam(models.Model):
    lahan = models.ForeignKey(Lahan, on_delete=models.CASCADE, related_name='musim_tanam_set', null=True, blank=True)
    nama_musim = models.CharField(max_length=100, help_text="Contoh: Mei - Agustus 2026")
    tanggal_mulai = models.DateField()
    tanggal_selesai = models.DateField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nama_musim} ({self.lahan.nama_lahan})"
    
class RiwayatChat(models.Model):
    ques = models.CharField(max_length=1000)
    answ = models.TextField()
    tgl = models.DateTimeField(auto_now_add=True)

#dashboard prediksi
class PrediksiInput(models.Model):
    lahan = models.ForeignKey(Lahan, on_delete=models.CASCADE, related_name='aktivitas_set')
    lokasi_aktivitas = models.CharField(max_length=150, blank=True, null=True)
    komoditas_aktivitas = models.CharField(max_length=100, blank=True, null=True)
    modal = models.DecimalField(max_digits=12, decimal_places=2, help_text="Input modal dalam Rupiah")
    luas_lahan = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Luas lahan yang digunakan dalam satuan meter persegi (m2)")
    tanggal_mulai_tanam = models.DateField(null=True, blank=True, help_text="Kapan mulai menanam")
    durasi_bulan = models.IntegerField(default=5, help_text="Durasi musim tanam dalam bulan")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Aktivitas Tanam"
#fitur prediksi Panen
class Lokasi(models.Model):
    country = models.CharField(max_length=100)
    provincy = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    
    def __str__(self):
        return f"{self.city} , {self.city}"
    
class MusimTanam2(models.Model):
    nama_panen = models.CharField(max_length=100)
    tanggal_mulai = models.DateField()
    tanggal_panen = models.DateField()
    
    def clean(self):
        if self.tanggal_mulai and self.tanggal_panen:
            if self.tanggal_panen < self.tanggal_mulai:
                raise ValidationError("Tanggal panen tidak boleh lebih awal dari tanggal mulai ")
            
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

class LuasLahan(models.Model):
    luas_meter = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    @property
    def luas_hektar(self):
        if self.luas_meter:
            return self.luas_meter / Decimal('10000')
        return Decimal('0.00')
    def __str__(self):
        return f"{self.luas_meter} m² ({self.luas_hektar} Ha)"
    
