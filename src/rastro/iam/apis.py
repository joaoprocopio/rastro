from http import HTTPStatus

from django.http import HttpRequest, HttpResponse

from rastro.common.apis import parse_body, require_POST, respond
from rastro.iam import deps, services
from rastro.iam.schemas import IdentityRegisterInput, SessionStartInput


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
