from datetime import timedelta
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from .managers import PersonManager


class Person(AbstractUser):
    username=None
    phone_number = models.CharField(max_length=15, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = PersonManager()

    def __str__(self):
        return f"{self.first_name} - {self.last_name}"


class Motorist(Person):
    id_type = models.CharField(max_length=30, blank=True,null=True,
                               choices=[('nida', 'kitambulisho cha nida'),
                                                       ('kura', 'kitambulisho cha mpiga kura'),
                                                       ('leseni', 'leseni ya udereva'), ('pasipoti', 'hati ya kusafiria')
                                                       ])
    id_number = models.CharField(max_length=50, unique=True, null=True, blank=True)

    class Meta:
        db_table = "motorists"

    def __str__(self):
        return f"{self.first_name} with id {self.id_number}"

class ParkingOperator(Person):
    company_name = models.CharField(max_length=30)
    business_telephone = models.CharField(max_length=15)
    business_email = models.EmailField(max_length=50)
    address = models.CharField(max_length=50)
    city =models.CharField(max_length=50)

    class Meta:
        db_table = "parking_operators"

    def __str__(self):
        return f"{self.first_name} operator for {self.company_name}"

class OTP(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="otps")
    otp_value = models.IntegerField()
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        expiry_time = self.created_at + timedelta(minutes=15)
        return timezone.now() > expiry_time

    def __str__(self):
        return f"{self.person.phone_number} - {self.otp_value}"

