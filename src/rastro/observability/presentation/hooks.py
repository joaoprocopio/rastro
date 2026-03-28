from typing import Callable

from django.http import HttpRequest, HttpResponse


def response_hook(span, request: HttpRequest, response: HttpResponse) -> None:
    if hasattr(request, "user") and request.user.is_authenticated:
        span.set_attribute("user.id", request.user.pk)
        span.set_attribute(
            "user.email", getattr(request.user, request.user.EMAIL_FIELD, "")
        )
        span.set_attribute("user.full_name", request.user.get_full_name())
