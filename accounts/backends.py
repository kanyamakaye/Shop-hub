from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q


class EmailOrUsernameModelBackend(ModelBackend):
    """Same as Django's default ModelBackend, but the login field matches either
    username or email — most people forget which one they registered with."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        if username is None or password is None:
            return None
        try:
            user = UserModel._default_manager.get(Q(username__iexact=username) | Q(email__iexact=username))
        except UserModel.DoesNotExist:
            UserModel().set_password(password)
            return None
        except UserModel.MultipleObjectsReturned:
            user = UserModel._default_manager.filter(
                Q(username__iexact=username) | Q(email__iexact=username)
            ).order_by('id').first()
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
