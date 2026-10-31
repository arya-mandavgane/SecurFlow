from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReleaseRequestViewSet

router = DefaultRouter()
router.register(r'', ReleaseRequestViewSet, basename='releases')

urlpatterns = [
    path('', include(router.urls)),
]
