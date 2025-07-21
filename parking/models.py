import math
import uuid
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from users.models import Motorist,ParkingOperator


# Create your models here.
class Vehicle(models.Model):
    VEHICLE_TYPES = [
        ('sedan', 'Sedan'),
        ('suv', 'SUV'),
        ('truck', 'Truck'),
        ('motorcycle', 'Motorcycle'),
        ('van', 'Van'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(Motorist, on_delete=models.CASCADE, related_name='vehicles')
    license_plate = models.CharField(max_length=20)
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPES)
    make = models.CharField(max_length=30, null=True, blank=True)
    model = models.CharField(max_length=30, null=True, blank=True)
    color = models.CharField(max_length=30, null=True, blank=True)

    class Meta:
        unique_together = ('user', 'license_plate')
        verbose_name = 'Vehicle'
        verbose_name_plural = 'Vehicles'

    def __str__(self):
        return f"{self.make} {self.model} ({self.license_plate})"


class ParkingLot(models.Model):
    name = models.CharField(max_length=50)
    address = models.CharField(max_length=100)
    operator = models.ForeignKey(ParkingOperator, on_delete=models.PROTECT, related_name="managed_lots", blank=True, null=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    total_spots = models.IntegerField(validators=[MinValueValidator(1)])
    description = models.TextField(max_length=500, blank=True)
    opening_hours = models.TimeField()
    closing_hours = models.TimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        indexes = [ models.Index(fields=['latitude', 'longitude']), ]
        verbose_name = 'Parking Lot'
        verbose_name_plural = 'Parking Lots'

    def __str__(self):
        return f"{self.name} (operator: {self.operator.company_name})"
    def clean(self):
        if self.opening_hours >= self.closing_hours:
            raise ValidationError("Closing hours must be after opening hours.")


class ParkingSpot(models.Model):
    SPOT_TYPES = [
        ('standard', 'Standard'),
        ('motorcycle', 'Motorcycle'),
        ('reserved', 'Reserved'),
    ]

    lot = models.ForeignKey(ParkingLot, on_delete=models.CASCADE, related_name='spots')
    spot_number = models.CharField(max_length=10)
    spot_type = models.CharField(max_length=20, choices=SPOT_TYPES)
    hourly_rate = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(1)])
    is_available = models.BooleanField(default=True)

    class Meta:
        unique_together = ('lot', 'spot_number')
        verbose_name = 'Parking Spot'
        verbose_name_plural = 'Parking Spots'

    def __str__(self):
        return f"{self.lot.name} - Spot {self.spot_number}"


class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(Motorist, on_delete=models.CASCADE, related_name='bookings')
    parking_spot = models.ForeignKey(ParkingSpot, on_delete=models.CASCADE, related_name='bookings')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='bookings')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    booking_time = models.DateTimeField(auto_now_add=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    cost = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    payment = models.OneToOneField('Payment', on_delete=models.SET_NULL, null=True, blank=True, related_name='booking')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    class Meta:
        unique_together = ('parking_spot', 'start_time', 'end_time')
        verbose_name = 'Booking'
        verbose_name_plural = 'Bookings'

    def __str__(self):
        return f"Booking {self.id} for {self.parking_spot} ({self.start_time})"

    def duration(self):
        """Calculate duration as a timedelta (not stored in DB)"""
        if self.end_time and self.start_time:
            return self.end_time - self.start_time
        return None

    def add_payment(self, payment):
        """Associate a payment with this booking"""
        self.payment = payment
        self.save()

    def clean(self):
        # Validate time sequence
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError("End time must be after start time.")

        # Check for overlapping bookings
        if self.parking_spot_id and self.start_time and self.end_time:
            overlapping = Booking.objects.filter(
                parking_spot=self.parking_spot,
                start_time__lt=self.end_time,
                end_time__gt=self.start_time
            ).exclude(id=self.id)

            if overlapping.exists():
                raise ValidationError("This parking spot is already booked for the selected time.")

    def save(self, *args, **kwargs):
        """Run full validation and calculate cost before saving"""
        self.full_clean()  # Enforces validation rules
        self.calculate_cost()
        super().save(*args, **kwargs)

    def calculate_cost(self):
        """Calculate booking cost based on parking spot rate and duration"""
        if self.start_time and self.end_time and self.parking_spot:
            duration = self.end_time - self.start_time
            hours = math.ceil(duration.total_seconds() / 3600)
            rate = getattr(self.parking_spot, 'hourly_rate', 0) or 0
            self.cost = hours * rate
        else:
            self.cost = 0


class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    amount = models.PositiveIntegerField(help_text="Amount in TZS")
    phone_number = models.CharField(max_length=15, help_text="Mobile money phone number")
    transaction_id = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
        ordering = ['-created_at']

    def __str__(self):
        return f"Payment {self.transaction_id} - {self.get_status_display()} (TZS {self.amount:,})"

    def clean(self):
        """Validate payment data"""
        errors = {}
        if self.amount <= 0:
            errors['amount'] = "Amount must be greater than zero."
        if errors:
            raise ValidationError(errors)

    @property
    def is_successful(self):
        return self.status == 'completed'

    @property
    def is_failed(self):
        return self.status == 'failed'

    def mark_completed(self):
        """Mark payment as successful"""
        self.status = 'completed'
        self.save()

    def get_amount_display(self):
        """Get formatted amount string"""
        return f"TZS {self.amount:,}"

