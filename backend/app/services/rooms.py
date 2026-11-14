"""ルームの作成・取得。"""

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models
from app.errors import ConflictError, NotFoundError


def list_rooms(db: Session) -> Sequence[models.Room]:
    return db.scalars(select(models.Room).order_by(models.Room.id)).all()


def get_room(db: Session, room_id: int) -> models.Room:
    room = db.get(models.Room, room_id)
    if room is None:
        raise NotFoundError(f"Room {room_id} not found")
    return room


def create_room(db: Session, name: str) -> models.Room:
    if db.scalar(select(models.Room).where(models.Room.name == name)) is not None:
        raise ConflictError(f"Room '{name}' already exists")
    room = models.Room(name=name)
    db.add(room)
    try:
        db.commit()
    except IntegrityError as e:  # 事前チェック後に同名ルームが同時作成された場合
        db.rollback()
        raise ConflictError(f"Room '{name}' already exists") from e
    return room


def ensure_room(db: Session, name: str) -> models.Room:
    """存在しなければ作成する（起動時のデフォルトルーム投入用）。"""
    room = db.scalar(select(models.Room).where(models.Room.name == name))
    return room if room is not None else create_room(db, name)
