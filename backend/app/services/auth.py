"""簡易認証：ユーザー名だけで入室し、セッショントークンを発行する。"""

import secrets

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models
from app.config import get_settings
from app.errors import UnauthorizedError
from app.services.memberships import add_member


def login(db: Session, name: str) -> tuple[str, models.User]:
    """ユーザーが存在しなければ作成し、新しいセッショントークンを発行する。"""
    user = _get_or_create_user(db, name)

    token = secrets.token_urlsafe(32)
    db.add(models.Session(token=token, user_id=user.id))
    db.commit()
    return token, user


def _get_or_create_user(db: Session, name: str) -> models.User:
    user = db.scalar(select(models.User).where(models.User.name == name))
    if user is not None:
        return user
    try:
        user = models.User(name=name)
        db.add(user)
        db.flush()
        _join_default_room(db, user)
        return user
    except IntegrityError:
        # 同名ユーザーが同時に作成された場合は、作成済みの方を使う
        db.rollback()
        return db.scalars(select(models.User).where(models.User.name == name)).one()


def _join_default_room(db: Session, user: models.User) -> None:
    """新規ユーザーは最初からデフォルトルームに参加させ、すぐ会話に入れるようにする。"""
    room = db.scalar(
        select(models.Room).where(models.Room.name == get_settings().default_room_name)
    )
    if room is not None:
        add_member(db, room.id, user.id)


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
