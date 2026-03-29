from .domain import (
    User,
    Credentials,
    UserRepository,
    AuthenticationError,
    UserNotFoundError,
    UserAlreadyExistsError,
    is_email,
)
from .application import (
    AuthenticateUserInput,
    CreateUserInput,
    UserOutput,
    AuthenticateUserUseCase,
    CreateUserUseCase,
    GetUserUseCase,
    get_authenticate_user_usecase,
    get_create_user_usecase,
    get_get_user_usecase,
)
from .infrastructure import (
    DjangoUserRepository,
    DjangoAuthService,
)
from .presentation import (
    EntrarForm,
    CadastrarForm,
    serialize_user,
    conta,
    entrar,
    cadastrar,
    sair,
)

__all__ = [
    # Domain
    "User",
    "Credentials",
    "UserRepository",
    "AuthenticationError",
    "UserNotFoundError",
    "UserAlreadyExistsError",
    "is_email",
    # Application
    "AuthenticateUserInput",
    "CreateUserInput",
    "UserOutput",
    "AuthenticateUserUseCase",
    "CreateUserUseCase",
    "GetUserUseCase",
    "get_authenticate_user_usecase",
    "get_create_user_usecase",
    "get_get_user_usecase",
    # Infrastructure
    "DjangoUserRepository",
    "DjangoAuthService",
    # Presentation
    "EntrarForm",
    "CadastrarForm",
    "serialize_user",
    "conta",
    "entrar",
    "cadastrar",
    "sair",
]
