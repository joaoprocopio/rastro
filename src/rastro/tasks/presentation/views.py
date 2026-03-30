from http import HTTPStatus

from django.http import HttpRequest, HttpResponse
from django.views import View


class Task(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        return HttpResponse(status=HTTPStatus.ACCEPTED)

    def post(self, request: HttpRequest) -> HttpResponse:
        return HttpResponse(status=HTTPStatus.IM_A_TEAPOT)
