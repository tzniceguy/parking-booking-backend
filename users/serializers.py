from rest_framework import serializers
from .models import Motorist, Person


class UserSerializer(serializers.ModelSerializer):
    """serializer class to serialize user details"""

    class Meta:
        model = Person
        fields = '__all__'

class MotoristRegistrationSerializer(serializers.ModelSerializer):
    """serializer class to serialize registration"""
    class Meta:
        model = Motorist
        fields = ("id", "first_name", "phone_number", "password")
        extra_kwargs = {
            "password": {"write_only": True},
            "first_name": {"required": True},
            "phone_number": {"required": True}
             }

    def validate_phone_number(self, value):
        if Person.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("Phone number already in use.")
        return value


    def create(self, validated_data):
        password = validated_data.pop('password')
        user = Motorist(**validated_data)
        user.set_password(password)
        user.save()
        return user

