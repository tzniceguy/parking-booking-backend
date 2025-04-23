from django.urls import path
from .views import MotoristRegistrationViewset

urlpatterns = [
    path('register/',MotoristRegistrationViewset.as_view(), name= "motorist-register" ),
]
