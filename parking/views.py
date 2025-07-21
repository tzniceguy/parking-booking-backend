from datetime import time
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from .serializers import ParkingLotSerializer, ParkingSpotSerializer, BookingSerializer, VehicleSerializer, \
    QuickBookingSerializer, PaymentSerializer
from rest_framework import viewsets,  mixins, status
from django_filters.rest_framework import DjangoFilterBackend
from .models import ParkingLot,  Booking, Vehicle, Payment
from .permissions import IsOperatorOrReadOnly
from rest_framework import permissions
from .utils import haversine_distance
from rest_framework.response import Response
from .utils import PaymentService

class ParkingLotViewSet(viewsets.ModelViewSet):
    serializer_class = ParkingLotSerializer
    queryset = ParkingLot.objects.filter(is_active=True)
    filter_backends = [DjangoFilterBackend]

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsOperatorOrReadOnly]
        else:
            self.permission_classes = [permissions.AllowAny]
        return super().get_permissions()

    def perform_create(self, serializer):
        if not hasattr(self.request.user, 'parkingoperator'):
            raise PermissionDenied("Only parking operators can create parking lots.")
        serializer.save(operator=self.request.user.parkingoperator)

    @action(detail=False, methods=['get'], url_path='search')
    def search(self, request):
        """
        Searches for parking lots based on a query, location, and radius.
        e.g., /api/parking/lots/search/?q=Kariakoo&lat=-6.76178824157151&lon=39.24324779774923&radius=5000
        """
        query = request.query_params.get("q")
        lat_str = request.query_params.get("lat")
        lon_str = request.query_params.get("lon")
        radius_str = request.query_params.get("radius", "5000")  # Default radius 5km

        if not all([lat_str, lon_str, radius_str]):
            return Response(
                {"error": "Missing required parameters: lat, lon, radius"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            lat, lon, radius = float(lat_str), float(lon_str), float(radius_str)
        except (ValueError, TypeError):
            return Response(
                {"error": "Invalid location or radius parameters."},
                status=status.HTTP_400_BAD_REQUEST
            )

        queryset = self.get_queryset()

        if query:
            queryset = queryset.filter(name__icontains=query) | queryset.filter(address__icontains=query)


        available_at = request.query_params.get("available_at")
        if available_at:
            try:
                check_time = time.fromisoformat(available_at)
                queryset = queryset.filter(opening_hours__lte=check_time, closing_hours__gte=check_time)
            except ValueError:
                return Response({"error": "Invalid time format for available_at. Use HH:MM."},
                                status=status.HTTP_400_BAD_REQUEST)

        nearby_lots = [
            lot for lot in queryset
            if haversine_distance(lat, lon, float(lot.latitude), float(lot.longitude)) <= radius
        ]

        serializer = self.get_serializer(nearby_lots, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='available-spots')
    def available_spots(self, request, pk=None):
        """
        Returns a list of available parking spots for a given parking lot.
        e.g., /api/parking/lots/{id}/available-spots/?spot_type=standard
        """
        parking_lot = self.get_object()
        spots = parking_lot.spots.filter(is_available=True)

        spot_type = request.query_params.get('spot_type')
        if spot_type:
            spots = spots.filter(spot_type=spot_type)

        serializer = ParkingSpotSerializer(spots, many=True)
        return Response(serializer.data)


class BookingViewSet(mixins.CreateModelMixin,
                   mixins.RetrieveModelMixin,
                   mixins.ListModelMixin,
                   viewsets.GenericViewSet):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        This view should return a list of all the bookings
        for the currently authenticated user.
        """
        return Booking.objects.filter(user=self.request.user).order_by('-booking_time')

    def perform_create(self, serializer):
        """
        Associate the booking with the logged-in user (Motorist).
        """
        if not hasattr(self.request.user, 'motorist'):
            raise PermissionDenied("Only motorists can make bookings.")

        # The serializer's validate method already checks if the vehicle belongs to the user
        serializer.save(user=self.request.user)

    def get_serializer_context(self):
        """
        Pass the request object to the serializer context.
        """
        return {'request': self.request}

    @action(detail=False, methods=['post'], url_path='quick-book')
    def quick_book(self, request):
        serializer = QuickBookingSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            booking = serializer.save()
            return Response(BookingSerializer(booking).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        """handle payment initialization for booking"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        booking = serializer.validated_data['booking']
        phone_number = serializer.validated_data['phone_number']

        try:
            booking = Booking.objects.get(id=serializer.validated_data['booking_id'])
            phone_number = serializer.validated_data['phone_number']

            payment_response = PaymentService.initiate_payment(
                phone_number=phone_number,
                amount=booking.cost,
                booking = booking.id,
            )

            if payment_response['success']:
                payment = Payment.objects.create(
                    amount=booking.cost,
                    phone_number=phone_number,
                    transaction_id=payment_response['transaction_id'],
                    booking=booking,
                    status="completed"  # Mark as completed directly
                )
                return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)

            # If payment initiation failed, return the error message from the service
            return Response({"error": payment_response.get('message', "Payment initiation failed.")}, status=status.HTTP_400_BAD_REQUEST)
        except Booking.DoesNotExist:
            return Response({"error": "Booking not found."}, status=status.HTTP_404_NOT_FOUND)





class VehicleViewSet(viewsets.ModelViewSet):
    serializer_class = VehicleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        This view should return a list of all the vehicles
        for the currently authenticated user.
        """
        return Vehicle.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """
        Associate the vehicle with the logged-in user (Motorist).
        """
        if not hasattr(self.request.user, 'motorist'):
            raise PermissionDenied("Only motorists can add vehicles.")
        serializer.save(user=self.request.user)
