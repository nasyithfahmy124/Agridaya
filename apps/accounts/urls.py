from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView,TokenRefreshView
from . import views
urlpatterns = [
    path('register/',views.RegisterAkun.as_view(),name='register'),
    path('login/',TokenObtainPairView.as_view(),name='login')
]
