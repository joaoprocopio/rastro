from typing import Callable
from http import HTTPStatus

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.contrib.auth.models import AnonymousUser


class AuthenticationMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        return self.get_response(request)


def require_authentication(view_func: Callable) -> Callable:
    def wrapped_view(request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if isinstance(request.user, AnonymousUser) or not request.user.is_authenticated:
            return JsonResponse(
                {"success": False, "error": "Authentication required"},
                status=HTTPStatus.UNAUTHORIZED,
            )
        return view_func(request, *args, **kwargs)

    return wrapped_view
