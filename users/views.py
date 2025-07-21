from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from rest_framework_simplejwt.tokens import RefreshToken
from .models import  OTP, Motorist
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_201_CREATED, HTTP_200_OK
from .serializers import MotoristRegistrationSerializer,  MotoristLoginSerializer, \
    OperatorRegisterSerializer, OperatorLoginSerializer, UserProfileSerializer, VerifyRegistrationOTPSerializer, CurrentUserSerializer
from rest_framework.generics import GenericAPIView
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny,  IsAuthenticated
from .utils import generate_otp, send_otp


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = CurrentUserSerializer(request.user)
        return Response(serializer.data)

class MotoristRegistrationView(GenericAPIView):
    """endpoint for the client to create the new user"""
    permission_classes = [AllowAny]
    serializer_class = MotoristRegistrationSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # Store registration data temporarily (you might want to use cache/session)
            phone_number = serializer.validated_data["phone_number"]

            # Generate and send OTP
            try:
                otp_value = generate_otp()
                if send_otp(phone_number, otp_value):
                    # Clear any existing OTPs for this phone number
                    OTP.objects.filter(phone_number=phone_number).delete()

                    # Save OTP to database
                    OTP.objects.create(
                        phone_number=phone_number,
                        otp=otp_value,
                        expires_at=timezone.now() + timedelta(minutes=15)
                    )

                    # Store registration data in session for later use
                    request.session['pending_registration'] = serializer.validated_data

                    return Response({
                        "message": "OTP sent successfully, please verify your phone number"
                    }, status=HTTP_200_OK)
                else:
                    return Response({
                        "message": "Failed to send OTP, please try again."
                    }, status=HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response({
                    "message": f"Error sending OTP: {str(e)}"
                }, status=HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)


class OTPVerificationView(GenericAPIView):
    """endpoint to verify the otp sent to the user and create the user record"""
    permission_classes = [AllowAny]
    serializer_class = VerifyRegistrationOTPSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            phone_number = serializer.validated_data['phone_number']

            # Get pending registration data
            pending_data = request.session.get('pending_registration')
            if not pending_data or pending_data['phone_number'] != phone_number:
                return Response({
                    "message": "No pending registration found for this phone number"
                }, status=HTTP_400_BAD_REQUEST)

            try:
                with transaction.atomic():
                    # Create the motorist
                    password = pending_data.pop('password')
                    motorist = Motorist(**pending_data)
                    motorist.set_password(password)
                    motorist.save()

                    # Clear session data
                    if 'pending_registration' in request.session:
                        del request.session['pending_registration']

                    # Generate tokens
                    refresh = RefreshToken.for_user(motorist)

                    return Response({
                        "message": "Motorist registered successfully",
                        "tokens": {
                            "access": str(refresh.access_token),
                            "refresh": str(refresh)
                        }
                    }, status=HTTP_201_CREATED)

            except Exception:
                return Response({
                    "message": "Registration failed"
                }, status=HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

class MotoristLoginView(APIView):
    """view to handle motorist login"""
    permission_classes = [AllowAny]

    def post(self,request):
        serializer = MotoristLoginSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.validated_data["user"]
            #refresh jwt tokens
            refresh = RefreshToken.for_user(user)
            return Response({
                "access":str(refresh.access_token),
                "refresh": str(refresh)
            }
            ,status = HTTP_200_OK)
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

class OperatorRegisterView(GenericAPIView):
    """view for registering an operator associated with parking"""
    permission_classes = [AllowAny]
    serializer_class = OperatorRegisterSerializer

    def post(self,request):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            operator = serializer.save()
            refresh = RefreshToken.for_user(operator)

            return Response(
                {
                    "message": "operator is registered successfully",
                    "tokens": {
                        "access": str(refresh.access_token),
                        "refresh":str(refresh)
                    },
                    "user": {
                        "id": operator.id,
                        "first_name": operator.first_name,
                        "phone_number": operator.phone_number,
                        "company": operator.company_name
                    }
                },status = HTTP_201_CREATED
            )
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

class OperatorLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self,request):
        serializer = OperatorLoginSerializer(data=request.data)

        if serializer.is_valid():
            operator = serializer.validated_data["user"]


            refresh = RefreshToken.for_user(operator)
            return Response({
                "message": "operator authenticated successfully",
                "tokens": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh)
                }, "user": {
                    "id": operator.id,
                    "first_name": operator.first_name,
                    "company_name": operator.company_name
                }
            }, status=HTTP_200_OK)
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self,request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        user = request.user
        serializer = UserProfileSerializer(user, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()

            # Update role-specific fields if needed
            if hasattr(user, 'motorist'):
                motorist = user.motorist
                allowed_fields = ['phone_number']
                for field in allowed_fields:
                    if field in request.data:
                        setattr(motorist, field, request.data[field])
                motorist.save()

            elif hasattr(user, 'parkingoperator'):
                operator = user.parkingoperator
                allowed_fields = ['business_email', 'phone_number', 'city']
                for field in allowed_fields:
                    if field in request.data:
                        setattr(operator, field, request.data[field])
                operator.save()

            return Response(serializer.data, status=HTTP_200_OK)

        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)


class ResendOTPView(APIView):
    """view to resend OTP for phone verification"""
    permission_classes = [AllowAny]

    def post(self, request):
        phone_number = request.data.get('phone_number')

        if not phone_number:
            return Response({
                "message": "Phone number is required"
            }, status=HTTP_400_BAD_REQUEST)

        # Check if there's pending registration
        pending_data = request.session.get('pending_registration')
        if not pending_data or pending_data['phone_number'] != phone_number:
            return Response({
                "message": "No pending registration found for this phone number"
            }, status=HTTP_400_BAD_REQUEST)

        # Generate and send new OTP
        otp_value = generate_otp()
        if send_otp(phone_number, otp_value):
            # Clear existing OTPs and create new one
            OTP.objects.filter(phone_number=phone_number).delete()
            OTP.objects.create(
                phone_number=phone_number,
                otp=otp_value,
                expires_at=timezone.now() + timedelta(minutes=15)
            )

            return Response({
                "message": "OTP resent successfully"
            }, status=HTTP_200_OK)
        else:
            return Response({
                "message": "Failed to send OTP, please try again"
            }, status=HTTP_400_BAD_REQUEST)