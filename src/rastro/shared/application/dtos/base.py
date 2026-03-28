from pydantic import BaseModel


class BaseResponse(BaseModel):
    success: bool = True
    message: str | None = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    code: str | None = None
