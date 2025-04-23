from django.core.serializers import get_serializer
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST,HTTP_201_CREATED
from .serializers import MotoristRegistrationSerializer
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny


# Create your views here.
class MotoristRegistrationViewset(GenericAPIView):
    """endpoint for client to create new user"""
    permission_classes = [AllowAny]
    serializer_class = MotoristRegistrationSerializer

    def post(self,request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            motorist = serializer.save()
            return Response({
                "message": "motorist registered successfully",
                "id": motorist.id
            },status=HTTP_201_CREATED)
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)