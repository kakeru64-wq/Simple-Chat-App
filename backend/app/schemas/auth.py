from pydantic import BaseModel

from app.schemas._common import ORMModel, UserName, UtcDatetime


class LoginRequest(BaseModel):
    name: UserName


class UserOut(ORMModel):
    id: int
    name: str
    created_at: UtcDatetime


class LoginResponse(BaseModel):
    token: str
    user: UserOut
