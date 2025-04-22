from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Vehicle)
admin.site.register(ParkingLot)
admin.site.register(ParkingSpot)
admin.site.register(Booking)
admin.site.register(Review)