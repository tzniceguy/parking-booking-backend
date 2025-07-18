from rest_framework import serializers
from .models import ParkingLot, ParkingSpot, Booking, Vehicle


class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = "__all__"
        read_only_fields = ('user',)


class ParkingSpotSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParkingSpot
        fields = ("id", "spot_number", "spot_type", "hourly_rate", "is_available")


class BookingSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    vehicle = serializers.PrimaryKeyRelatedField(
        queryset=Vehicle.objects.all(),
        help_text="The ID of the vehicle to book the spot for."
    )
    parking_spot = serializers.PrimaryKeyRelatedField(
        queryset=ParkingSpot.objects.all(),
        help_text="The ID of the parking spot being booked."
    )

    class Meta:
        model = Booking
        fields = (
            "id",
            "user",
            "parking_spot",
            "vehicle",
            "start_time",
            "end_time",
            "duration",
            "cost",
            "status",
            "booking_time",
        )
        read_only_fields = ("id", "user", "duration", "cost", "status", "booking_time")

    def validate(self, data):
        # Check if the spot is available
        spot = data.get("parking_spot")
        if not spot.is_available:
            raise serializers.ValidationError("This parking spot is not currently available.")

        # Check for overlapping bookings
        start_time = data.get("start_time")
        end_time = data.get("end_time")
        overlapping_bookings = Booking.objects.filter(
            parking_spot=spot,
            start_time__lt=end_time,
            end_time__gt=start_time,
            status__in=['confirmed', 'active']
        ).exists()

        if overlapping_bookings:
            raise serializers.ValidationError("This parking spot is already booked for the selected time.")

        # Ensure the vehicle belongs to the user
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            if data["vehicle"].user != request.user:
                raise serializers.ValidationError("You can only book with a vehicle registered to your account.")

        return data


class ParkingLotSerializer(serializers.ModelSerializer):
    operator_name = serializers.CharField(source="operator.company_name", read_only=True)
    available_spots_count = serializers.SerializerMethodField()

    class Meta:
        model = ParkingLot
        fields = (
            "id",
            "name",
            "address",
            "latitude",
            "longitude",
            "operator_name",
            "available_spots_count",
            "opening_hours",
            "closing_hours",
            "is_active",
        )
        read_only_fields = ("id", "created_at")

    def get_available_spots_count(self, obj):
        return obj.spots.filter(is_available=True).count()
