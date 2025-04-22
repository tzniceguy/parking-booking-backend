

from django.contrib import admin

from .models import Person, Motorist, OTP

admin.site.register(Person)
admin.site.register(Motorist)
admin.site.register(OTP)