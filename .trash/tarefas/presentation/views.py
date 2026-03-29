from http import HTTPStatus
from typing import TYPE_CHECKING, cast

from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from pydantic import ValidationError

from rastro.tarefas.domain.exceptions import (
    TaskNotFoundError,
    TaskNotOwnedError,
    TaskAlreadyDeletedError,
)
from rastro.tarefas.application.dto import (
    CreateTaskInput,
    UpdateTaskInput,
    GetTaskInput,
    DeleteTaskInput,
    ListTasksInput,
)
from rastro.tarefas.application.exceptions import TaskValidationError
from rastro.tarefas.application.use_cases.list_tasks import get_list_tasks_usecase
from rastro.tarefas.application.use_cases.create_task import get_create_task_usecase
from rastro.tarefas.application.use_cases.update_task import get_update_task_usecase
from rastro.tarefas.application.use_cases.delete_task import get_delete_task_usecase
from rastro.tarefas.application.use_cases.get_task import get_get_task_usecase
from rastro.tarefas.infrastructure.error_inducers import (
    always_break,
    break_50_percent,
    break_randomly,
)
from rastro.tarefas.presentation.forms import CreateTaskForm, UpdateTaskForm
from rastro.tarefas.presentation.serializers import serialize_task, serialize_tasks

if TYPE_CHECKING:
    from django.contrib.auth.models import User


def _get_user_id(request: WSGIRequest) -> int:
    user: "User" = cast("User", request.user)  # type: ignore[union-attr]
    return user.id  # type: ignore[union-attr]


def _is_authenticated(request: WSGIRequest) -> bool:
    return request.user.is_authenticated  # type: ignore[union-attr]


@require_GET
def list_tasks(request: WSGIRequest):
    if not _is_authenticated(request):
        return HttpResponse(status=HTTPStatus.UNAUTHORIZED)

    use_case = get_list_tasks_usecase()
    tasks = use_case.execute(ListTasksInput(owner_id=_get_user_id(request)))

    return JsonResponse(serialize_tasks(tasks), status=HTTPStatus.OK, safe=False)


@require_POST
@csrf_exempt
def create_task(request: WSGIRequest):
    if not _is_authenticated(request):
        return HttpResponse(status=HTTPStatus.UNAUTHORIZED)

    try:
        form = CreateTaskForm.model_validate_json(request.body)
        use_case = get_create_task_usecase()

        task = use_case.execute(
            CreateTaskInput(
                title=form.title,
                description=form.description,
                owner_id=_get_user_id(request),
            )
        )

        return JsonResponse(serialize_task(task), status=HTTPStatus.CREATED)
    except ValidationError as exc:
        return HttpResponse(
            exc.json().encode(),
            status=HTTPStatus.BAD_REQUEST,
            content_type="application/json",
        )
    except TaskValidationError as exc:
        return HttpResponse(
            str(exc),
            status=HTTPStatus.BAD_REQUEST,
        )


@require_GET
def get_task(request: WSGIRequest, task_id: int):
    if not _is_authenticated(request):
        return HttpResponse(status=HTTPStatus.UNAUTHORIZED)

    try:
        use_case = get_get_task_usecase()
        task = use_case.execute(
            GetTaskInput(task_id=task_id, owner_id=_get_user_id(request))
        )
        return JsonResponse(serialize_task(task), status=HTTPStatus.OK)
    except TaskNotFoundError:
        return HttpResponse(status=HTTPStatus.NOT_FOUND)
    except TaskNotOwnedError:
        return HttpResponse(status=HTTPStatus.FORBIDDEN)


@require_http_methods(["PATCH"])
@csrf_exempt
def update_task(request: WSGIRequest, task_id: int):
    if not _is_authenticated(request):
        return HttpResponse(status=HTTPStatus.UNAUTHORIZED)

    try:
        form = UpdateTaskForm.model_validate_json(request.body)
        use_case = get_update_task_usecase()

        task = use_case.execute(
            UpdateTaskInput(
                task_id=task_id,
                owner_id=_get_user_id(request),
                title=form.title,
                description=form.description,
                status=form.status,
            )
        )

        return JsonResponse(serialize_task(task), status=HTTPStatus.OK)
    except ValidationError as exc:
        return HttpResponse(
            exc.json().encode(),
            status=HTTPStatus.BAD_REQUEST,
            content_type="application/json",
        )
    except TaskNotFoundError:
        return HttpResponse(status=HTTPStatus.NOT_FOUND)
    except TaskNotOwnedError:
        return HttpResponse(status=HTTPStatus.FORBIDDEN)


@require_POST
@csrf_exempt
def delete_task(request: WSGIRequest, task_id: int):
    if not _is_authenticated(request):
        return HttpResponse(status=HTTPStatus.UNAUTHORIZED)

    try:
        use_case = get_delete_task_usecase()
        use_case.execute(
            DeleteTaskInput(task_id=task_id, owner_id=_get_user_id(request))
        )
        return HttpResponse(status=HTTPStatus.NO_CONTENT)
    except TaskNotFoundError:
        return HttpResponse(status=HTTPStatus.NOT_FOUND)
    except TaskNotOwnedError:
        return HttpResponse(status=HTTPStatus.FORBIDDEN)
    except TaskAlreadyDeletedError:
        return HttpResponse(status=HTTPStatus.CONFLICT)


@require_GET
def always_break_endpoint(request: WSGIRequest):
    always_break()
    return HttpResponse(status=HTTPStatus.OK)


@require_GET
def break_50_percent_endpoint(request: WSGIRequest):
    break_50_percent()
    return HttpResponse(status=HTTPStatus.OK)


@require_GET
def break_randomly_endpoint(request: WSGIRequest):
    break_randomly()
    return HttpResponse(status=HTTPStatus.OK)
