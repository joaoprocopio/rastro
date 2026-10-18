from http import HTTPStatus

from django.http import HttpRequest, HttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie

from rastro.common.views import parse_body, require_GET, require_POST, respond
from rastro.iam import deps, selectors, services
from rastro.iam.schemas import (
    IdentityRegisterInput,
    SessionCurrentOutput,
    SessionStartInput,
)


@require_POST
def identity_register_view(request: HttpRequest) -> HttpResponse:
    body = parse_body(request, IdentityRegisterInput)
    services.identity_register(
        email=body.email,
        display_name=body.display_name,
        password=body.password,
        password_hasher=deps.PASSWORD_HASHER,
    )
    return respond(status=HTTPStatus.CREATED)


@require_POST
def session_start_view(request: HttpRequest) -> HttpResponse:
    body = parse_body(request, SessionStartInput)
    services.session_start(
        request=request,
        email=body.email,
        password=body.password,
        authenticator=deps.AUTHENTICATE,
        session_store=deps.SESSION_STORE,
    )
    return respond(status=HTTPStatus.NO_CONTENT)


@require_GET
def session_current_view(request: HttpRequest) -> HttpResponse:
    identity = selectors.identity_get_current(
        request=request, session_store=deps.SESSION_STORE
    )
    output = SessionCurrentOutput.model_validate(identity)
    return respond(status=HTTPStatus.OK, output=output)


@require_POST
def session_end_view(request: HttpRequest) -> HttpResponse:
    services.session_end(request=request, session_store=deps.SESSION_STORE)
    return respond(status=HTTPStatus.NO_CONTENT)


@require_GET
@ensure_csrf_cookie
def csrf_get_view(request: HttpRequest) -> HttpResponse:
    return respond(status=HTTPStatus.NO_CONTENT)
