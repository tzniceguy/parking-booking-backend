from django.urls import path
from .views import MotoristRegistrationView, UsersListView, MotoristLoginView, OperatorRegisterView, OperatorLoginView, \
    UserProfileView

urlpatterns = [
    path('users/', UsersListView.as_view(), name="list-users"),
    path('register/',MotoristRegistrationView.as_view(), name= "motorist-register" ),
    path('login/', MotoristLoginView.as_view(), name = "motorist-login"),
    path('operator-register/', OperatorRegisterView.as_view(), name="operator-login"),
    path('operator-login/', OperatorLoginView.as_view(), name = "operator-login"),
    path('profile/', UserProfileView.as_view(), name="user-profile")
]
