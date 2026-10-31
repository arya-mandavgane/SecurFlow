from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NotificationViewSet, AlertRuleViewSet

router = DefaultRouter()
router.register(r'rules', AlertRuleViewSet, basename='alert-rules')
router.register(r'', NotificationViewSet, basename='notifications')

urlpatterns = [
    path('', include(router.urls)),
]
