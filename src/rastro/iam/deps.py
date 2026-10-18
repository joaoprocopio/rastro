from rastro.iam.adapters import django_make_password
from rastro.iam.ports import PasswordHasher

PASSWORD_HASHER: PasswordHasher = django_make_password
