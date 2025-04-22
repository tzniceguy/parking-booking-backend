from django.shortcuts import render
from .serializers import UserRegistrationSerializer
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny


# Create your views here.
class UserRegistrationViewSet(GenericAPIView):
    """endpoint for client to create new user"""
    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer
