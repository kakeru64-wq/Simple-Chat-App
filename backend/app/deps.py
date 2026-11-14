"""FastAPI の依存関数（認証など）。"""

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app import models
from app.db import get_db
from app.errors import UnauthorizedError
from app.services import auth as auth_service

_bearer = HTTPBearer(auto_error=False)

DbSession = Annotated[Session, Depends(get_db)]


def get_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> str:
    if credentials is None:
        raise UnauthorizedError("Not authenticated")
    return credentials.credentials


def get_current_user(db: DbSession, token: Annotated[str, Depends(get_token)]) -> models.User:
    return auth_service.get_user_by_token(db, token)


CurrentUser = Annotated[models.User, Depends(get_current_user)]
Token = Annotated[str, Depends(get_token)]
