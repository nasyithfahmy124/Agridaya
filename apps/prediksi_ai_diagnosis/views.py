from django.shortcuts import render
from .serializers import AktivitasTanamSeri,PrediksiInput,AIDiagnosisSerializer
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
import os
import json
import logging
from django.conf import settings
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
import google.generativeai as genai
from .models import AIDiagnosis

class AktivitasView(viewsets.ModelViewSet):
    serializer_class = AktivitasTanamSeri
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PrediksiInput.objects.filter(user=self.request.user)
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)



logger = logging.getLogger(__name__)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

class AIDiagnosisViewSet(viewsets.ModelViewSet):
    queryset = AIDiagnosis.objects.all()
    serializer_class = AIDiagnosisSerializer
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        user_crop_name = request.data.get('crop_name', '').strip()
        
        try:
            instance.image.open('rb')
            image_data = instance.image.read()
            instance.image.close()
            
            image_parts = [
                {
                    "mime_type": "image/jpeg",
                    "data": image_data
                }
            ]
            
            model = genai.GenerativeModel(
                model_name="gemini-2.5-flash",
                generation_config={"response_mime_type": "application/json"}
            )
            
            prompt = f"""
            Anda adalah pakar agronomi internasional untuk platform pertanian Agridaya.
            Tugas Anda adalah menganalisis foto yang diberikan secara ketat.

            --- ATURAN VALIDASI ---
            1. Periksa apakah foto ini benar-benar menampilkan tanaman atau bagian dari tanaman (daun, batang, buah, bunga, akar).
            2. Jika objek dalam foto adalah MANUSIA, HEWAN, BENDA MATI, MAKANAN OLAHAN, atau APA PUN selain tanaman hidup, Anda HARUS menyetel nilai key "is_valid_plant" menjadi false.
            3. Jika objek adalah tanaman, setel "is_valid_plant" menjadi true.

            --- DETAIL DIAGNOSIS ---
            4. Jika "is_valid_plant" adalah true:
            - Jika input nama tanaman dari user adalah "{user_crop_name}" (kosongkan jika tidak ada), gunakan informasi tersebut.
            - Jika input nama tanaman kosong atau tidak diberikan, Anda wajib MENDETEKSI dan MENYEBUTKAN jenis tanamannya pada key "detected_crop_name" (contoh: "Jagung", "Padi", "Tomat").
            - Identifikasi penyakit tanaman tersebut beserta skor keyakinan, tingkat keparahan, perkiraan area terinfeksi, dan daftar solusi pencegahan yang komprehensif.

            Anda HARUS mengembalikan struktur JSON murni persis seperti berikut:
            {{
                "is_valid_plant": true atau false,
                "detected_crop_name": "Nama jenis tanaman yang dideteksi (diisi hanya jika input tanaman kosong/tidak akurat)",
                "diagnosis": {{
                    "penyakit": "Nama Penyakit (Nama Latin jika ada)",
                    "skor_keyakinan": "Skor keyakinan analisis Anda dalam persentase (contoh: 94%)",
                    "tingkat_keparahan": "Kritis / Sedang / Ringan",
                    "area_terinfeksi": "Perkiraan persentase area tanaman yang terinfeksi (contoh: ~12.5%)",
                    "solusi_pencegahan": [
                        "Langkah solusi ke-1",
                        "Langkah solusi ke-2"
                    ]
                }}
            }}

            Jika "is_valid_plant" bernilai false, Anda tidak perlu mengisi objek "diagnosis" (cukup isi dengan null) dan "detected_crop_name" kosongkan saja.
            Jangan memberikan teks penjelasan apapun di luar JSON.
            """
            
            response = model.generate_content([image_parts[0], prompt])
            raw_json = json.loads(response.text)
            
            if not raw_json.get("is_valid_plant", True):
                instance.delete()
                return Response(
                    {
                        "error": "Gambar ditolak.",
                        "details": "Objek yang Anda unggah bukan merupakan tanaman. AI Agridaya hanya mendeteksi penyakit tanaman."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            if not user_crop_name:
                detected_crop = raw_json.get("detected_crop_name", "Tanaman Tidak Dikenal")
                instance.crop_name = detected_crop
    
            instance.diagnosis_result = raw_json.get("diagnosis")
            instance.save()
            
            return_serializer = self.get_serializer(instance)
            return Response(return_serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            
            if instance.id:
                instance.delete()
            logger.error(f"Error AI Diagnosis: {str(e)}")
            return Response(
                {"error": "Terjadi kegagalan saat memproses diagnosis.", "details": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )