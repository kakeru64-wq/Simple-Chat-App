from fastapi import APIRouter, status

from app import schemas
from app.deps import CurrentUser, DbSession, Token
from app.services import auth as auth_service

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=schemas.LoginResponse)
def login(body: schemas.LoginRequest, db: DbSession) -> schemas.LoginResponse:
    """ユーザー名で入室する。未登録の名前なら新規ユーザーを作成する。"""
    token, user = auth_service.login(db, body.name)
    return schemas.LoginResponse(token=token, user=schemas.UserOut.model_validate(user))


@router.get("/me", response_model=schemas.UserOut)
def me(user: CurrentUser):
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(db: DbSession, token: Token) -> None:
    auth_service.logout(db, token)
