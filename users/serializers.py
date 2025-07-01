from django.contrib.auth import authenticate
from rest_framework import serializers
from .models import Motorist, Person, ParkingOperator, OTP


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
        motorist = Motorist(**validated_data)
        motorist.set_password(password)
        motorist.save()
        return motorist



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

class OTPSerializer(serializers.ModelSerializer):
    """serializer for OTP"""
    phone_number = serializers.CharField(max_length=15)

class VerifyRegistrationOTPSerializer(serializers.Serializer):
    """serializer for OTP verificatiion"""
    phone_number = serializers.CharField()
    otp = serializers.IntegerField()


    def validate(self,attrs):
        phone_number = attrs.get('phone_number')
        otp = attrs.get('otp')

        try:
            otp_object = OTP.objects.get(phone_number=phone_number, otp=otp, is_used=False)
        except OTP.DoesNotExist:
            raise serializers.ValidationError("invalid otp")

        if otp_object.is_expired():
            raise serializers.ValidationError("OTP has expired")

        otp_object.is_used = True
        otp_object.save()

        return attrs

    def create(self,validated_data):
        phone_number = validated_data.get('phone_number')
        user = Person.objects.get(phone_number=phone_number)

        # If the user does not exist, raise an error
        if not user:
            raise serializers.ValidationError("User does not exist")

        # Return the user object
        return user

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

class OperatorLoginSerializer(serializers.Serializer):
    """serializer for authenticating parking operators"""
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
            operator = ParkingOperator.objects.get(pk=user.pk)
        except ParkingOperator.DoesNotExist:
            raise serializers.ValidationError("not a registered operator")

        attrs["user"] = operator
        return attrs

class UserProfileSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    extra_data = serializers.SerializerMethodField()

    class Meta:
        model = Person
        fields = ("id", "first_name", "last_name", "phone_number", "role", "extra_data")
        read_only_fields=("id", "phone_number")

    # Method to get the user role from person object
    def get_role(self, obj):
        if hasattr(obj, 'motorist'):
            return "motorist"
        if hasattr(obj, 'parkingoperator'):
            return "parking operator"
        return "user"

    # Method to get extra fields for user object
    def get_extra_data(self, obj):
        if hasattr(obj, 'motorist'):
            return {
                "id_type": obj.motorist.id_type,
                "id_number": obj.motorist.id_number
            }
        if hasattr(obj, 'parkingoperator'):
            return {
                "company_name": obj.parkingoperator.company_name,
                "business_email": obj.parkingoperator.business_email,
                "city": obj.parkingoperator.city,
            }
        return {}
