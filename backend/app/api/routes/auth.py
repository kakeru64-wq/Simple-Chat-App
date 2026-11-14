"""/api/auth : 入室（ログイン）・現在のユーザー・ログアウト"""

from fastapi import APIRouter, status

from app import schemas
from app.api.deps import CurrentUser, DbSession, Token
from app.services import auth

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=schemas.LoginResponse)
def login(body: schemas.LoginRequest, db: DbSession):
    """ユーザー名で入室する。未登録の名前なら新しいユーザーを作成する。"""
    token, user = auth.login(db, body.name)
    return schemas.LoginResponse(token=token, user=schemas.UserOut.model_validate(user))


@router.get("/me", response_model=schemas.UserOut)
def me(user: CurrentUser):
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(db: DbSession, token: Token) -> None:
    auth.logout(db, token)
