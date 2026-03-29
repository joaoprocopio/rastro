from django.contrib import auth
from django.http import HttpRequest

from rastro.conta.application.dto import UserOutput


class DjangoAuthService:
    def login(self, request: HttpRequest, user: UserOutput) -> None:
        django_user = self._get_django_user(user.id)
        auth.login(request, django_user)

    def logout(self, request: HttpRequest) -> None:
        auth.logout(request)

    def _get_django_user(self, user_id: int):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        return User.objects.get(id=user_id)
