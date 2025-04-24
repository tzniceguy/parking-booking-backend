from rest_framework.routers import DefaultRouter
from .views import ParkingLotViewSet

router = DefaultRouter()
router.register(r'lots', ParkingLotViewSet, basename='lots')

urlpatterns = []
urlpatterns += router.urls
