from django.urls import path
from .views import FarmIdentityView,CultivationLogListView
app_name = "farm_identity"

urlpatterns = [
    path("farm-identity/", FarmIdentityView.as_view(), name="farm-identity-detail"),
    path('log-budidaya/', CultivationLogListView.as_view(), name='cultivation-logs'),
]