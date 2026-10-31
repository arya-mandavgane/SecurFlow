from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RenewalViewSet

router = DefaultRouter()
router.register(r'', RenewalViewSet, basename='renewals')

urlpatterns = [
    path('', include(router.urls)),
]
