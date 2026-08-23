from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

UserModel = get_user_model()


class CaseInsensitiveModelBackend(ModelBackend):
    """
    Authenticate users with case-insensitive usernames.
    Allows students to type 'roll_01', 'Roll_01', or 'ROLL_01' seamlessly.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None

        try:
            # Case-insensitive lookup
            user = UserModel.objects.get(username__iexact=username.strip())
        except UserModel.DoesNotExist:
            UserModel().set_password(password)  # Prevent timing attack
            return None
        except UserModel.MultipleObjectsReturned:
            # If multiple exist with different casing, take exact first, then first
            user = UserModel.objects.filter(username=username.strip()).first()
            if not user:
                user = UserModel.objects.filter(username__iexact=username.strip()).first()

        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None
