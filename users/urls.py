from django.urls import path
from .views import MotoristRegistrationView, UsersListView, MotoristLoginView, OperatorRegisterView

urlpatterns = [
    path('users/', UsersListView.as_view(), name="list-users"),
    path('register/',MotoristRegistrationView.as_view(), name= "motorist-register" ),
    path('login/', MotoristLoginView.as_view(), name = "motorist-login"),
    path('register-operator/', OperatorRegisterView.as_view(), name="operator=login")
]
