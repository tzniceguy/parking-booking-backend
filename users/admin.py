from datetime import timedelta, timezone

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Person, Motorist, OTP


# Admin configuration for Person
@admin.register(Person)
class PersonAdmin(UserAdmin):
    model = Person

    # Fields shown in the admin page list view
    list_display = ('phone_number', 'first_name', 'last_name', 'email', 'is_staff', 'is_active', 'created_at')

    # Filters available on the right side of the admin list page
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'created_at')

    # Field sections on the admin detail page
    fieldsets = (
        (None, {'fields': ('phone_number', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined', 'created_at')}),
    )

    # Fields for the user creation form (in admin)
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone_number', 'first_name', 'last_name', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )

    # Fields admin can search by
    search_fields = ('phone_number', 'first_name', 'last_name', 'email')

    # Default order in list view
    ordering = ('-created_at',)


# Admin configuration for Motorist
@admin.register(Motorist)
class MotoristAdmin(admin.ModelAdmin):
    # Display fields from Person (inherited) in the list view
    list_display = ('phone_number', 'first_name', 'last_name', 'is_active', 'created_at')

    # Search by Person fields
    search_fields = ('phone_number', 'first_name', 'last_name')

    # Filters for Motorist
    list_filter = ('is_active', 'created_at')

    # Make fields read-only
    readonly_fields = ('created_at',)

    # Fieldsets for detailed view
    fieldsets = (
        (None, {'fields': ('phone_number', 'first_name', 'last_name')}),
        ('Status', {'fields': ('is_active', 'created_at')}),
    )


# Admin configuration for OTP
@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    # Display OTP details in the list view
    list_display = ('person', 'otp_value', 'is_used', 'created_at', 'is_expired', 'time_until_expiry')

    # Search by Person's phone_number and OTP value
    search_fields = ('person__phone_number', 'otp_value')

    # Filters for OTP
    list_filter = ('is_used', 'created_at')

    # Make created_at read-only
    readonly_fields = ('created_at',)

    # Fieldsets for detailed view
    fieldsets = (
        (None, {'fields': ('person', 'otp_value', 'is_used')}),
        ('Timestamps', {'fields': ('created_at',)}),
    )

    def time_until_expiry(self, obj):
        if obj.is_expired():
            return "Expired"
        expiry_time = obj.created_at + timedelta(minutes=15)
        remaining = expiry_time - timezone.now()
        return f"{remaining.seconds // 60} minutes remaining"

    time_until_expiry.short_description = "Time Until Expiry"