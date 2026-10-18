import pytest
from django.urls import reverse


@pytest.mark.parametrize(
    ("name", "path"),
    [
        ("iam:identity_register", "/api/v1/iam/identities/register"),
        ("iam:session_current", "/api/v1/iam/session"),
        ("iam:session_start", "/api/v1/iam/session/start"),
        ("iam:session_end", "/api/v1/iam/session/end"),
        ("iam:csrf_get", "/api/v1/iam/csrf"),
    ],
)
def test_every_url_has_a_name_in_the_iam_namespace(name: str, path: str) -> None:
    assert reverse(name) == path
