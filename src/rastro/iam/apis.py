from http import HTTPStatus

from django.http import HttpRequest, HttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie

from rastro.common.apis import parse_body, require_GET, require_POST, respond
from rastro.iam import deps, selectors, services
from rastro.iam.schemas import (
    IdentityRegisterInput,
    SessionCurrentOutput,
    SessionStartInput,
)


@require_POST
def identity_register_api(request: HttpRequest) -> HttpResponse:
    input = parse_body(request, IdentityRegisterInput)
    services.identity_register(
        email=input.email,
        display_name=input.display_name,
        password=input.password,
        password_hasher=deps.PASSWORD_HASHER,
    )
    return respond(status=HTTPStatus.CREATED)


@require_POST
def session_start_api(request: HttpRequest) -> HttpResponse:
    input = parse_body(request, SessionStartInput)
    services.session_start(
        request=request,
        email=input.email,
        password=input.password,
        authenticator=deps.AUTHENTICATE,
        session_store=deps.SESSION_STORE,
    )
    return respond(status=HTTPStatus.NO_CONTENT)


@require_GET
def session_current_api(request: HttpRequest) -> HttpResponse:
    identity = selectors.identity_get_current(
        request=request, session_store=deps.SESSION_STORE
    )
    output = SessionCurrentOutput(
        email=identity.email, display_name=identity.display_name
    )
    return respond(status=HTTPStatus.OK, output=output)


@require_POST
def session_end_api(request: HttpRequest) -> HttpResponse:
    services.session_end(request=request, session_store=deps.SESSION_STORE)
    return respond(status=HTTPStatus.NO_CONTENT)


@require_GET
@ensure_csrf_cookie
def csrf_get_api(request: HttpRequest) -> HttpResponse:
    return respond(status=HTTPStatus.NO_CONTENT)
