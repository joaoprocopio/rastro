from http import HTTPStatus

from django.http import JsonResponse


def handle_404(request, exception=None) -> JsonResponse:
    return JsonResponse(
        {"success": False, "error": "Not found", "code": "NOT_FOUND"},
        status=HTTPStatus.NOT_FOUND,
    )


def handle_500(request, exception=None) -> JsonResponse:
    return JsonResponse(
        {"success": False, "error": "Internal server error", "code": "INTERNAL_ERROR"},
        status=HTTPStatus.INTERNAL_SERVER_ERROR,
    )


def handle_403(request, exception=None) -> JsonResponse:
    return JsonResponse(
        {"success": False, "error": "Forbidden", "code": "FORBIDDEN"},
        status=HTTPStatus.FORBIDDEN,
    )


def handle_401(request, exception=None) -> JsonResponse:
    return JsonResponse(
        {"success": False, "error": "Unauthorized", "code": "UNAUTHORIZED"},
        status=HTTPStatus.UNAUTHORIZED,
    )
