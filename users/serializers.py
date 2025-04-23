from django.contrib.auth import authenticate
from rest_framework import serializers
from .models import Motorist, Person,ParkingOperator


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

class MotoristLoginSerializer(serializers.Serializer):
    """serializer to handle motorist registration"""
    phone_number = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self,attrs):
        phone_number = attrs.get('phone_number')
        password = attrs.get('password')
        if not phone_number or not password:
            raise serializers.ValidationError("both phone number and password field are required")

        #authenticate user and return
        user = authenticate(username=phone_number, password=password)

        if not user:
            raise serializers.ValidationError("invalid credentials")

        try:
            motorist = Motorist.objects.get(pk=user.pk)
        except Motorist.DoesNotExist:
            raise serializers.ValidationError("not a registered motorist")

        attrs["user"] = user
        return attrs

class OperatorRegisterSerializer(serializers.ModelSerializer):
    """serializer for registering parking operator"""
    class Meta:
        model = ParkingOperator
        fields = ("id", "first_name", "phone_number", "company_name", "password")
        extra_kwargs = {
            "password": {"write_only": True},
            "first_name": {"required": True},
            "phone_number": {"required": True},
            "company_name": {"required": True}
        }

    def validate_phone_number(self, value):
        if ParkingOperator.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("Phone number already in use.")
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = ParkingOperator(**validated_data)
        user.set_password(password)
        user.save()
        return user