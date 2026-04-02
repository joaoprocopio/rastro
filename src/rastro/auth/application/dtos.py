from pydantic import BaseModel


class SignUpInput(BaseModel):
    username: str
    email: str
    password: str


class SignInInput(BaseModel):
    query: str
    password: str


class UserOutput(BaseModel):
    id: int
    email: str
    username: str
    password: str
    is_active: bool


class UserPublic(BaseModel):
    email: str
    username: str
