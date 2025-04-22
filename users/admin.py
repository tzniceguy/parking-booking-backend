

from django.contrib import admin

from .models import Person, Motorist, OTP, ParkingOperator

admin.site.register(Person)
admin.site.register(Motorist)
admin.site.register(OTP)
admin.site.register(ParkingOperator)