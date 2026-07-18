from django.contrib import admin
from django.urls import path,include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls')),
    path('',include('apps.accounts.urls')),
    path('',include('apps.marketplace.urls')),
    path('',include('apps.prediksi_ai_diagnosis.urls')),
    path('',include('apps.farm_identity.urls')),
    path('',include('apps.pendanaan.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
