from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.views import APIView
from .models import Produk,Order
from .serializers import ProdukSeri,OrderSeri
from django.db.models import Q

class CreateProduk(APIView):
    serializer_class = ProdukSeri
    permission_classes = [IsAuthenticated]
    def get(self, request):
        kategori_dipilih= request.query_params.get('kategori',None)
        cari_produk = request.query_params.get('search',None)
        
        semua_produk = Produk.objects.all().order_by('-tgl')
        if kategori_dipilih :
            semua_produk = semua_produk.filter(kategori=kategori_dipilih).order_by('-tgl')
        if cari_produk:
            semua_produk =semua_produk.filter(
                Q(nama__icontains=cari_produk) | Q(deskripsi__icontains=cari_produk)
            )
            
        semua_produk = semua_produk.order_by('-tgl')
        serializer = ProdukSeri(semua_produk,many=True,context={'request': request})
        return Response(serializer.data,status=status.HTTP_200_OK)
    
    def post(self,request):
        produk = ProdukSeri(data = request.data)
        if produk.is_valid():
            produk.save(penjual = request.user)
            return Response(
                {"message":"produk berhasil dibuat!"},
                status=status.HTTP_201_CREATED
                )
        return Response(produk.errors,status=status.HTTP_400_BAD_REQUEST)
    
    
class OrderView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        #riwayat order
        riwayat = Order.objects.all().order_by('-tgl')
        serializer = OrderSeri(riwayat,many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)
    def post(self, request):
        serializer = OrderSeri(data=request.data)
        if serializer.is_valid():
            produk_obj = serializer.validated_data['produk']
            produk_qty = serializer.validated_data['qty']
            
            if produk_obj.stok < produk_qty:
                return Response(
                    {"error": f"Stok tidak mencukupi. Sisa stok: {produk_obj.stok}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                produk_obj.stok -= produk_qty
                produk_obj.save()
                serializer.save(buyer=request.user if request.user.is_authenticated else None)
                
                return Response(
                    {"message": "berhasil!", "sisa_stok": produk_obj.stok},
                    status=status.HTTP_201_CREATED
                )
                
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    