from django.shortcuts import render
from .serializers import AktivitasTanamSeri,PrediksiInput
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

class AktivitasView(viewsets.ModelViewSet):
    serializer_class = AktivitasTanamSeri
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PrediksiInput.objects.filter(user=self.request.user)
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)