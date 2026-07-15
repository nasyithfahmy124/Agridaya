from django.contrib import admin
from django.urls import path,include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls')),
    path('',include('apps.accounts.urls')),
    path('',include('apps.marketplace.urls')),
    path('',include('apps.prediksi_ai_diagnosis.urls')),
    path('',include('apps.farm_identity.urls'))
]
