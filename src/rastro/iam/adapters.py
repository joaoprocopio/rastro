from django.contrib.auth.hashers import make_password

from rastro.iam.ports import PasswordHasher
from rastro.iam.values import HashedPassword, RawPassword


def django_make_password(*, password: RawPassword) -> HashedPassword:
    return HashedPassword(make_password(password.value))


_: PasswordHasher = django_make_password
