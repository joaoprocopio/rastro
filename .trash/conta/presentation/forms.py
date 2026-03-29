from pydantic import BaseModel, Field


class EntrarForm(BaseModel):
    query: str = Field(min_length=1)
    password: str = Field(min_length=1)


class CadastrarForm(BaseModel):
    first_name: str = Field(min_length=1)
    last_name: str = Field(min_length=1)
    username: str = Field(min_length=3)
    email: str = Field(pattern=r".*@.*")
    password: str = Field(min_length=8)
