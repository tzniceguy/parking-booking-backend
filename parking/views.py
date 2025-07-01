from datetime import time

from rest_framework.exceptions import PermissionDenied

from .serializers import ParkingLotSerializer
from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import ParkingLot
from .permissions import IsOperatorOrReadOnly
from rest_framework import permissions
from .utils import haversine_distance

# Create your views here.
class ParkingLotViewSet(viewsets.ModelViewSet):
    serializer_class = ParkingLotSerializer
    queryset = ParkingLot.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = []
    search_fields = ['name', 'address']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsOperatorOrReadOnly()]
        return [permissions.AllowAny()]

    def perform_create(self, serializer):
        if not self.request.user.is_authenticated:
            raise PermissionDenied("You must be logged in to create a parking lot")

        if not hasattr(self.request.user, 'parkingoperator'):
            raise PermissionDenied("Only parking operators can create parking lots")

        serializer.save(operator=self.request.user.parkingoperator)

    def get_queryset(self):
        queryset = super().get_queryset()
        lat = self.request.query_params.get("lat")
        lon = self.request.query_params.get("lon")
        radius = self.request.query_params.get("radius")
        available_at = self.request.query_params.get("available_at")

        # Apply time-based filtering first while it's still a queryset
        if available_at:
            try:
                check_time = time.fromisoformat(available_at)
                queryset = queryset.filter(opening_hours__lte=check_time, closing_hours__gte=check_time)
            except ValueError:
                pass  # Ignore filtering if time format is wrong

        # Apply distance filtering last since it converts to Python list
        if lat and lon and radius:
            try:
                lat, lon, radius = float(lat), float(lon), float(radius)
                filtered_lots = []
                for lot in queryset:
                    distance = haversine_distance(
                        lat, lon, float(lot.latitude), float(lot.longitude)
                    )
                    if distance <= radius:
                        filtered_lots.append(lot)
                return filtered_lots
            except ValueError:
                pass  # Ignore filtering if params are invalid

        return queryset