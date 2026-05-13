from pydantic import BaseModel, ConfigDict, Field


class UserCreate(BaseModel):
    login: str = Field(min_length=8, max_length=8)
    password: str = Field(min_length=8, max_length=128)
    last_name: str = Field(max_length=50)
    first_name: str = Field(max_length=50)
    organization: str = Field(max_length=50)
    email: str = Field(max_length=50)
    role: str = Field(default="user", pattern="^(admin|user)$")


class UserOut(BaseModel):
    id: int
    login: str
    last_name: str
    first_name: str
    organization: str
    email: str
    role: str

    model_config = ConfigDict(from_attributes=True)


class PasswordResetIn(BaseModel):
    new_password: str = Field(min_length=8, max_length=128)


class StatusOut(BaseModel):
    status: str = "ok"