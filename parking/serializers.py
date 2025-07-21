from datetime import  timedelta
from django.utils import timezone
from rest_framework import serializers
from .models import ParkingLot, ParkingSpot, Booking, Vehicle, Payment
import re

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

class QuickBookingSerializer(serializers.Serializer):
    license_plate = serializers.CharField(max_length=20)
    phone_number = serializers.CharField(max_length=15)
    parking_lot = serializers.PrimaryKeyRelatedField(queryset=ParkingLot.objects.all())
    parking_spot = serializers.PrimaryKeyRelatedField(
        queryset=ParkingSpot.objects.all(),
        required=True
    )
    start_time = serializers.DateTimeField()
    end_time = serializers.DateTimeField()

    def validate(self, data):
        """
        Comprehensive validation for the booking
        """
        # Time validation
        if data['start_time'] >= data['end_time']:
            raise serializers.ValidationError("End time must be after start time.")

        if data['start_time'] < timezone.now():
            raise serializers.ValidationError("Cannot book for past times.")

        # Minimum booking duration (5 minutes)
        if (data['end_time'] - data['start_time']) < timedelta(minutes=5):
            raise serializers.ValidationError("Minimum booking duration is  minutes.")

        # Spot validation
        parking_spot = data['parking_spot']
        parking_lot = data['parking_lot']

        if parking_spot.lot != parking_lot:
            raise serializers.ValidationError(
                f"Spot {parking_spot.spot_number} does not belong to {parking_lot.name}"
            )

        if not parking_spot.is_available:
            raise serializers.ValidationError(
                f"Spot {parking_spot.spot_number} is not available"
            )

        # Check for overlapping bookings
        overlapping = Booking.objects.filter(
            parking_spot=parking_spot,
            start_time__lt=data['end_time'],
            end_time__gt=data['start_time'],
            status__in=['confirmed', 'active']
        ).exists()

        if overlapping:
            raise serializers.ValidationError(
                f"Spot {parking_spot.spot_number} is already booked for the selected time"
            )

        return data

    def validate_license_plate(self, value):
        """License plate normalization and validation"""
        value = value.strip().upper()
        if not value:
            raise serializers.ValidationError("License plate cannot be empty.")
        return value

    def create(self, validated_data):
        request = self.context['request']

        # Get or create vehicle with defaults
        vehicle, _ = Vehicle.objects.get_or_create(
            license_plate=validated_data["license_plate"],
            user=request.user.motorist,
            defaults={
                'vehicle_type': 'sedan',
                'make': 'Unknown',
                'model': 'Unknown',
                'color': 'Unknown',
            }
        )

        # Create booking with calculated cost
        booking = Booking.objects.create(
            user=request.user.motorist,
            parking_spot=validated_data["parking_spot"],
            vehicle=vehicle,
            phone_number=validated_data["phone_number"],
            start_time=validated_data["start_time"],
            end_time=validated_data["end_time"],
            status='confirmed',
        )

        # Update spot availability
        validated_data["parking_spot"].is_available = False
        validated_data["parking_spot"].save()

        return booking

class PaymentSerializer(serializers.ModelSerializer):
    booking_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Payment
        fields = ["id", "phone_number", "booking_id", "amount", "transaction_id", "status", "created_at", "updated_at"]
        read_only_fields = ["id", "amount", "transaction_id", "status", "created_at", "updated_at"]

    def validate_phone_number(self, phone_number):
        """validate and format phone number"""
        phone_number = phone_number.strip().replace(" ", "")

        #handle the local format and remove the + if it exists
        if phone_number.startswith("0") and len(phone_number) == 10:
            phone_number = "255" + phone_number[1:]
        phone_number = phone_number.lstrip("+")
        if not re.fullmatch(r"\d{10,14}", phone_number):
            raise serializers.ValidationError("Invalid phone number format. It should be 10 to 14 digits long.")

        return phone_number

    def validate_amount(self, amount):
        """validate amount to be a positive number"""
        if amount <= 0:
            raise serializers.ValidationError("Amount must be a positive number.")
        return amount
