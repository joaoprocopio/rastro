import random
from http import HTTPStatus

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from rastro.auth.infrastructure.services import DjangoSessionService
from rastro.tasks.application.dtos import CreateTaskInput, UpdateTaskInput
from rastro.tasks.application.use_cases import (
    CreateTaskUseCase,
    DeleteTaskUseCase,
    GetTaskUseCase,
    ListTasksUseCase,
    UpdateTaskUseCase,
)
from rastro.tasks.domain.errors import (
    AlwaysBreakError,
    Break50PercentError,
    BreakRandomlyError,
    TaskNotFoundError,
    TaskPermissionError,
)
from rastro.tasks.infrastructure.repositories import DjangoTaskRepository
from rastro.tasks.presentation.presenters import TaskListPresenter, TaskPresenter
from rastro_base.entity import Id


@method_decorator(csrf_exempt, name="dispatch")  # type: ignore[misc]
class TaskListView(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        session_service = DjangoSessionService(request)
        user = session_service.logged_user()

        if user is None:
            return HttpResponse(status=HTTPStatus.UNAUTHORIZED)

        repository = DjangoTaskRepository()
        use_case = ListTasksUseCase(repository)
        output = use_case.execute(user.id)

        return JsonResponse(TaskListPresenter.present(output), status=HTTPStatus.OK)

    def post(self, request: HttpRequest) -> HttpResponse:
        session_service = DjangoSessionService(request)
        user = session_service.logged_user()

        if user is None:
            return HttpResponse(status=HTTPStatus.UNAUTHORIZED)

        repository = DjangoTaskRepository()
        use_case = CreateTaskUseCase(repository)
        input_dto = CreateTaskInput.parse_json(request.body)
        output = use_case.execute((user.id, input_dto))

        return JsonResponse(TaskPresenter.present(output), status=HTTPStatus.CREATED)


@method_decorator(csrf_exempt, name="dispatch")  # type: ignore[misc]
class TaskDetailView(View):
    def get(self, request: HttpRequest, task_id: int) -> HttpResponse:
        session_service = DjangoSessionService(request)
        user = session_service.logged_user()

        if user is None:
            return HttpResponse(status=HTTPStatus.UNAUTHORIZED)

        repository = DjangoTaskRepository()
        use_case = GetTaskUseCase(repository)

        try:
            output = use_case.execute((Id(task_id), user.id))
            return JsonResponse(TaskPresenter.present(output), status=HTTPStatus.OK)
        except TaskNotFoundError:
            return HttpResponse(status=HTTPStatus.NOT_FOUND)
        except TaskPermissionError:
            return HttpResponse(status=HTTPStatus.FORBIDDEN)

    def put(self, request: HttpRequest, task_id: int) -> HttpResponse:
        session_service = DjangoSessionService(request)
        user = session_service.logged_user()

        if user is None:
            return HttpResponse(status=HTTPStatus.UNAUTHORIZED)

        repository = DjangoTaskRepository()
        use_case = UpdateTaskUseCase(repository)
        input_dto = UpdateTaskInput.parse_json(request.body)

        try:
            output = use_case.execute((Id(task_id), user.id, input_dto))
            return JsonResponse(TaskPresenter.present(output), status=HTTPStatus.OK)
        except TaskNotFoundError:
            return HttpResponse(status=HTTPStatus.NOT_FOUND)
        except TaskPermissionError:
            return HttpResponse(status=HTTPStatus.FORBIDDEN)

    def delete(self, request: HttpRequest, task_id: int) -> HttpResponse:
        session_service = DjangoSessionService(request)
        user = session_service.logged_user()

        if user is None:
            return HttpResponse(status=HTTPStatus.UNAUTHORIZED)

        repository = DjangoTaskRepository()
        use_case = DeleteTaskUseCase(repository)

        try:
            use_case.execute((Id(task_id), user.id))
            return HttpResponse(status=HTTPStatus.NO_CONTENT)
        except TaskNotFoundError:
            return HttpResponse(status=HTTPStatus.NOT_FOUND)
        except TaskPermissionError:
            return HttpResponse(status=HTTPStatus.FORBIDDEN)


class AlwaysBreakView(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        raise AlwaysBreakError()


class Break50PercentView(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        if random.random() < 0.5:
            raise Break50PercentError()

        return HttpResponse(status=HTTPStatus.OK)


class BreakRandomlyView(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        if random.random() < random.random():
            raise BreakRandomlyError()

        return HttpResponse(status=HTTPStatus.OK)
