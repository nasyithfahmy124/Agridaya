from django.conf import settings
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible
from supabase import create_client, Client

@deconstructible
class SupabaseStorage(Storage):
    def __init__(self):
        self.url = getattr(settings, "SUPABASE_URL", None)
        self.key = getattr(settings, "SUPABASE_KEY", None)
        self.bucket_name = getattr(settings, "SUPABASE_BUCKET_NAME", "media")

        if not self.url or not self.key:
            raise ValueError(
                "SUPABASE_URL dan SUPABASE_KEY tidak ditemukan di settings.py! "
                "Pastikan sudah dikonfigurasi dengan benar."
            )
            
        self.client: Client = create_client(self.url, self.key)
    def _open(self, name, mode='rb'):
        try:
            response = self.client.storage.from_(self.bucket_name).download(name)
            from io import BytesIO
            return BytesIO(response)
        except Exception as e:
            raise IOError(f"Gagal membaca file dari Supabase: {e}")

    def _save(self, name, content):
        # Dipanggil otomatis oleh Django saat ImageField disimpan
        try:
            file_data = content.read()
            # Gunakan content-type yang sesuai (default: octet-stream atau deteksi manual)
            content_type = getattr(content, 'content_type', 'image/jpeg')
            
            self.client.storage.from_(self.bucket_name).upload(
                path=name,
                file=file_data,
                file_options={"content-type": content_type, "upsert": "true"}
            )
            return name
        except Exception as e:
            raise IOError(f"Gagal upload file ke Supabase: {e}")

    def exists(self, name):
        # Mengecek apakah file sudah ada di bucket Supabase
        try:
            # Mengambil list file di path tersebut untuk memeriksa eksistensi
            path_parts = name.rsplit('/', 1)
            folder = path_parts[0] if len(path_parts) > 1 else ""
            file_name = path_parts[-1]
            
            res = self.client.storage.from_(self.bucket_name).list(folder)
            for item in res:
                if item.get('name') == file_name:
                    return True
            return False
        except Exception:
            return False

    def url(self, name):
        # Mengembalikan public URL agar image_url/file_url bisa diakses via API
        return self.client.storage.from_(self.bucket_name).get_public_url(name)