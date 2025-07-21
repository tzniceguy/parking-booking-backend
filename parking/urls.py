from rest_framework.routers import DefaultRouter
from .views import ParkingLotViewSet, BookingViewSet, VehicleViewSet,PaymentViewSet

router = DefaultRouter()
router.register(r'lots', ParkingLotViewSet, basename='parkinglot')
router.register(r'bookings', BookingViewSet, basename='booking')
router.register(r'vehicles', VehicleViewSet, basename='vehicle')
router.register(r'payments', PaymentViewSet, basename='payment')

urlpatterns = router.urls
