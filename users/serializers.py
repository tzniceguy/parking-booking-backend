from rest_framework import serializers
from .models import Person

class UserSerializer(serializers.ModelSerializer):
    """serializer class to serialize user details"""

    class Meta:
        model = Person
        fields = '__all__'

class UserRegistrationSerializer(serializers.ModelSerializer):
    """serializer class to serialize registration"""
    class Meta:
        model = Person
        fields = ("id", "first_name", "phone_number", "password")
        extra_kwargs = {"password": {"write_only": True}}

    def create(self,validated_data):
        return Person.objects.create_user(**validated_data)