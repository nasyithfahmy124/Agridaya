# File: backend/custom_storage.py
import os
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible
from supabase import create_client, Client

@deconstructible
class SupabaseStorage(Storage):
    def __init__(self):
        self.supabase_url = os.environ.get("SUPABASE_URL")
        self.key = os.environ.get("SUPABASE_KEY")
        self.bucket_name = os.environ.get("SUPABASE_BUCKET_NAME", "agridaya")
        self.client: Client = create_client(self.supabase_url, self.key)

    def _open(self, name, mode='rb'):
        try:
            clean_name = name.replace('\\', '/')
            response = self.client.storage.from_(self.bucket_name).download(clean_name)
            from io import BytesIO
            return BytesIO(response)
        except Exception as e:
            raise IOError(f"Gagal membaca file dari Supabase: {e}")

    def _save(self, name, content):
        try:
            clean_name = name.replace('\\', '/')
            
            file_data = content.read()
            content_type = getattr(content, 'content_type', 'image/jpeg')
            
            self.client.storage.from_(self.bucket_name).upload(
                path=clean_name,
                file=file_data,
                file_options={"content-type": content_type, "upsert": "true"}
            )
            return clean_name
        except Exception as e:
            raise IOError(f"Gagal mengunggah file ke Supabase: {e}")

    def exists(self, name):
        try:
            clean_name = name.replace('\\', '/')
            path_parts = clean_name.rsplit('/', 1)
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
        try:
            clean_name = name.replace('\\', '/')
            response = self.client.storage.from_(self.bucket_name).get_public_url(clean_name)
            if isinstance(response, dict):
                return response.get("publicUrl", "")
            return str(response)
        except Exception:
            return ""