import math
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from users.models import Motorist


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
    make = models.CharField(max_length=30)
    model = models.CharField(max_length=30)
    color = models.CharField(max_length=30)

    class Meta:
        unique_together = ('user', 'license_plate')
        verbose_name = 'Vehicle'
        verbose_name_plural = 'Vehicles'

    def __str__(self):
        return f"{self.make} {self.model} ({self.license_plate})"


class ParkingLot(models.Model):
    name = models.CharField(max_length=50)
    address = models.CharField(max_length=100)
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
        return self.name
    def clean(self):
        if self.opening_hours >= self.closing_hours:
            raise ValidationError("Closing hours must be after opening hours.")


class ParkingSpot(models.Model):
    SPOT_TYPES = [
        ('standard', 'Standard'),
        ('compact', 'Compact'),
        ('handicap', 'Handicap'),
        ('electric', 'Electric Vehicle'),
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
    booking_time = models.DateTimeField(auto_now_add=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    duration = models.DurationField()
    cost = models.DecimalField(max_digits=8, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    class Meta:
        unique_together = ('parking_spot', 'start_time', 'end_time')
        verbose_name = 'Booking'
        verbose_name_plural = 'Bookings'

    def __str__(self):
        return f"Booking {self.id} for {self.parking_spot} ({self.start_time})"

    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError("End time must be after start time.")
        # Check for overlapping bookings
        overlapping_bookings = Booking.objects.filter(
            parking_spot=self.parking_spot,
            start_time__lt=self.end_time,
            end_time__gt=self.start_time,
        ).exclude(id=self.id)
        if overlapping_bookings.exists():
            raise ValidationError("This parking spot is already booked for the selected time.")

    def save(self, *args, **kwargs):
        # Compute duration
        if  self.end_time and self.start_time:
            self.duration = self.end_time - self.start_time
            #compute costs round up to nearlest hour
            if self.parking_spot and self.parking_spot.hourly_rate is not None and self.duration:
                total_seconds = self.duration.total_seconds()
                hours = math.ceil(total_seconds/3600)
                self.cost = hours * self.parking_spot.hourly_rate
            else:
                self.cost = 0
        else:
            self.cost = 0

        super().save(*args, **kwargs)

class Review(models.Model):
    booking = models.ForeignKey(Booking,on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(Motorist, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('booking', 'user')
        verbose_name = 'Review'
        verbose_name_plural = 'Reviews'

    def clean(self):
        # Ensure the reviewer is the user associated with the booking
        if self.booking_id and self.user_id:
            if self.user != self.booking.user:
                raise ValidationError("You can only review your own bookings.")

    def __str__(self):
        return f"Review {self.rating}/5 by {self.user} for Booking {self.booking.id}"