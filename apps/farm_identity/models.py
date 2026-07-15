from django.db import models
from django.contrib.auth import get_user_model
PLACEHOLDER_KOORDINAT = "-7.25, 112.76"

User = get_user_model()
class FarmerProfile(models.Model):
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name="farmer_profile"
    )
    nama_petani = models.CharField(max_length=150)
    foto_profil = models.ImageField(
        upload_to="profiles/",
        blank=True,
        null=True,
        help_text="Upload foto profil petani (opsional).",
    )
    tahun_pengalaman = models.PositiveIntegerField(default=0)
    komoditas_utama = models.CharField(
        max_length=200,
        blank=True,
        help_text="Contoh: Padi, Jagung, Kopi",
    )
    deskripsi_singkat = models.TextField(
        blank=True,
        help_text="Bio singkat petani untuk ditampilkan di halaman profil.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Profil Petani"
        verbose_name_plural = "Profil Petani"
        ordering = ["-updated_at"]

    def __str__(self):
        return self.nama_petani


class FarmIdentity(models.Model):
    farmer = models.OneToOneField(
        FarmerProfile,
        on_delete=models.CASCADE,
        related_name="farm_identity",
    )
    nama_lahan = models.CharField(max_length=150)
    luas_lahan = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        help_text="Luas lahan dalam hektar (Ha).",
    )
    tipe_tanah = models.CharField(max_length=100)
    lokasi_daerah = models.CharField(
        max_length=150,
        help_text="Contoh: 'Surabaya, Jawa Timur'",
    )
    koordinat_dummy = models.CharField(
        max_length=50,
        blank=True,
        help_text="Teks koordinat simulasi (tidak dihitung otomatis, hanya placeholder).",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Identitas Lahan"
        verbose_name_plural = "Identitas Lahan"
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.nama_lahan} ({self.lokasi_daerah})"

    def save(self, *args, **kwargs):
        if not self.koordinat_dummy:
            self.koordinat_dummy = PLACEHOLDER_KOORDINAT
        super().save(*args, **kwargs)
        
#aktivitas log 
class CultivationLog(models.Model):
    farm_identity = models.ForeignKey(
        FarmIdentity, 
        on_delete=models.CASCADE, 
        related_name="logs"
    )
    tanggal = models.DateField(
        help_text="Tanggal dan waktu aktivitas dilakukan."
    )
    aktivitas = models.CharField(
        max_length=100,
        help_text="Contoh: Irigasi, Pemupukan, Penanaman, Pemanenan"
    )
    input_digunakan = models.CharField(
        max_length=200,
        help_text="Bahan yang digunakan. Contoh: Air Sungai (Sekunder), Kompos Organik"
    )
    catatan_lapangan = models.TextField(
        help_text="Detail catatan aktivitas selama di lapangan."
    )
    dokumentasi = models.ImageField(
        upload_to="dokumentasi/",
        help_text="Wajib mengunggah foto bukti dokumentasi kegiatan lapangan."
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-tanggal"]
        verbose_name = "Log Budidaya"
        verbose_name_plural = "Log Budidaya"

    def __str__(self):
        return f"{self.aktivitas}"