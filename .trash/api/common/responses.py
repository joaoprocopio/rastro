from http import HTTPStatus
from typing import Any
from django.http import JsonResponse


def success_response(data: Any, status: int = HTTPStatus.OK) -> JsonResponse:
    return JsonResponse(
        {
            "success": True,
            "data": data,
        },
        status=status,
    )


def error_response(
    error: str,
    code: str | None = None,
    status: int = HTTPStatus.BAD_REQUEST,
) -> JsonResponse:
    return JsonResponse(
        {
            "success": False,
            "error": error,
            "code": code,
        },
        status=status,
    )


def paginated_response(
    items: list[Any],
    page: int,
    per_page: int,
    total: int,
) -> JsonResponse:
    total_pages = (total + per_page - 1) // per_page
    return JsonResponse(
        {
            "success": True,
            "data": items,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
            },
        }
    )
