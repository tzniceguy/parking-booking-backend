from django.urls import path
from .views import MotoristRegistrationView, UsersListView, MotoristLoginView

urlpatterns = [
    path('users/', UsersListView.as_view(), name="list-users"),
    path('register/',MotoristRegistrationView.as_view(), name= "motorist-register" ),
    path('login/', MotoristLoginView.as_view(), name = "motorist-login"),
]
