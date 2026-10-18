from http import HTTPStatus

from django.http import HttpRequest, HttpResponse

from rastro.common.apis import parse_body, require_POST, respond
from rastro.iam import deps, services
from rastro.iam.schemas import SessionStartInput


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
