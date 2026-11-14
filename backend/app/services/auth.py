"""簡易認証：ユーザー名だけで入室し、セッショントークンを発行する。"""

import secrets

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models
from app.core.errors import UnauthorizedError


def login(db: Session, name: str) -> tuple[str, models.User]:
    """名前のユーザーを取得（なければ作成）し、新しいセッショントークンを発行する。"""
    user = _get_or_create_user(db, name)
    token = secrets.token_urlsafe(32)
    db.add(models.Session(token=token, user_id=user.id))
    db.commit()
    return token, user


def get_user_by_token(db: Session, token: str) -> models.User:
    session = db.get(models.Session, token)
    if session is None:
        raise UnauthorizedError("Invalid or expired token")
    return session.user


def logout(db: Session, token: str) -> None:
    session = db.get(models.Session, token)
    if session is not None:
        db.delete(session)
        db.commit()


def _get_or_create_user(db: Session, name: str) -> models.User:
    user = db.scalar(select(models.User).where(models.User.name == name))
    if user is not None:
        return user
    try:
        user = models.User(name=name)
        db.add(user)
        db.flush()
        return user
    except IntegrityError:
        # 同じ名前のユーザーが同時に作成された場合は、作成済みの方を使う
        db.rollback()
        return db.scalars(select(models.User).where(models.User.name == name)).one()
