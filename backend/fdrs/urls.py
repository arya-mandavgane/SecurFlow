from rest_framework.routers import DefaultRouter
from .views import FDRViewSet

router = DefaultRouter()
router.register(r'', FDRViewSet, basename='fdr')

urlpatterns = router.urls
