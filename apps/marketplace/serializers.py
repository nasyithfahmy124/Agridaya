from rest_framework import serializers
from .models import Produk,Order
class ProdukSeri(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    class Meta:
        model = Produk
        fields = ['id','nama','kategori','deskripsi','price','image','stok']
    def get_image(self, obj):
        if obj.image:
            return f"/media/{obj.image.name}"
        return None
        
class OrderSeri(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['produk','qty']