from django.contrib.auth.backends import BaseBackend
from users.models import Person

class PhoneNumberBackend(BaseBackend):
    def authenticate(self, request, phone_number=None, password=None, **kwargs):
        try:
            user = Person.objects.get(phone_number=phone_number)
            if user.check_password(password):
                return user
        except Person.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return Person.objects.get(pk=user_id)
        except Person.DoesNotExist:
            return None