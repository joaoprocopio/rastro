from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist

from rastro.conta.domain.entities import User
from rastro.conta.domain.repositories import UserRepository


class DjangoUserRepository(UserRepository):
    def __init__(self):
        self.User = get_user_model()

    def get_by_id(self, user_id: int) -> User | None:
        try:
            user = self.User.objects.get(id=user_id)
            return self._to_domain(user)
        except ObjectDoesNotExist:
            return None

    def get_by_email(self, email: str) -> User | None:
        try:
            user = self.User.objects.get(email=email)
            return self._to_domain(user)
        except ObjectDoesNotExist:
            return None

    def get_by_username(self, username: str) -> User | None:
        try:
            user = self.User.objects.get(username=username)
            return self._to_domain(user)
        except ObjectDoesNotExist:
            return None

    def create(
        self,
        first_name: str,
        last_name: str,
        username: str,
        email: str,
        password: str,
    ) -> User:
        user = self.User.objects.create_user(
            first_name=first_name,
            last_name=last_name,
            username=username,
            email=email,
            password=password,
        )
        return self._to_domain(user)

    def verify_password(self, user: User, password: str) -> bool:
        try:
            django_user = self.User.objects.get(id=user.id)
            return django_user.check_password(password)
        except ObjectDoesNotExist:
            return False

    def _to_domain(self, django_user) -> User:
        return User(
            id=django_user.id,
            username=django_user.username,
            email=django_user.email,
            first_name=django_user.first_name,
            last_name=django_user.last_name,
        )
