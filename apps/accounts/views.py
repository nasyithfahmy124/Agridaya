from django.shortcuts import render
from rest_framework.views import APIView
from .serializers import RegisterSeri
from rest_framework.response import Response
from rest_framework import status
# Create your views here.
class RegisterAkun(APIView):
    def post(self,request):
        seri = RegisterSeri(data=request.data)
        if seri.is_valid():
            seri.save()
            return Response(
                {'message' : 'akun  berhasil dibuat!'},
                status=status.HTTP_200_OK
            )
        return Response(seri.errors,status=status.HTTP_400_BAD_REQUEST)