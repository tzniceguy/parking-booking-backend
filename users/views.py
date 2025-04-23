from rest_framework_simplejwt.tokens import RefreshToken

from .models import Person
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_201_CREATED, HTTP_200_OK
from .serializers import MotoristRegistrationSerializer, UserSerializer, MotoristLoginSerializer
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny,IsAdminUser


# Create your views here.
class UsersListView(ListAPIView):
    """endpoint to retrieve users in our system"""
    permission_classes = [IsAdminUser]
    serializer_class = UserSerializer
    queryset = Person.objects.all()

class MotoristRegistrationView(GenericAPIView):
    """endpoint for client to create new user"""
    permission_classes = [AllowAny]
    serializer_class = MotoristRegistrationSerializer

    def post(self,request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            motorist = serializer.save()
            refresh = RefreshToken.for_user(motorist)
            return Response({
                "message": "motorist registered successfully",
                "token":{
                    "access":str(refresh.access_token),
                    "refresh":str(refresh)
                },
                "id": motorist.id
            },status=HTTP_201_CREATED)
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
                "message": "user authenticated successfully",
                "tokens":{
                    "access":str(refresh.access_token),
                    "refresh": str(refresh)
                },"user":{
                    "id": user.id,
                    "first_name": user.first_name,
                    "phone_number":user.phone_number
                }
            },status = HTTP_200_OK)
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

