"""ルートで使う依存関数。`db: DbSession`、`user: CurrentUser` のように型注釈で受け取る。"""

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app import models
from app.core.database import get_db
from app.core.errors import UnauthorizedError
from app.services import auth

_bearer = HTTPBearer(auto_error=False)

DbSession = Annotated[Session, Depends(get_db)]


def get_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> str:
    """`Authorization: Bearer <token>` ヘッダーからトークンを取り出す。"""
    if credentials is None:
        raise UnauthorizedError("Not authenticated")
    return credentials.credentials


def get_current_user(db: DbSession, token: Annotated[str, Depends(get_token)]) -> models.User:
    return auth.get_user_by_token(db, token)


Token = Annotated[str, Depends(get_token)]
CurrentUser = Annotated[models.User, Depends(get_current_user)]
