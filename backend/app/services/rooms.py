"""ルームの作成と名前変更。"""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models
from app.core.errors import ConflictError
from app.services.room_access import get_room, require_member
from app.services.system_messages import add_system_message


def create_room(db: Session, name: str, creator: models.User) -> models.Room:
    """ルームを作成し、作成者を参加させる（作成時は「参加しました」を記録しない）。"""
    _ensure_name_available(db, name)
    room = models.Room(name=name)
    db.add(room)
    db.flush()  # room.id を確定させる
    db.add(models.RoomMember(room_id=room.id, user_id=creator.id))
    _commit_or_conflict(db, name)
    return room


def rename_room(
    db: Session, room_id: int, user: models.User, name: str
) -> tuple[models.Room, models.Message | None]:
    """ルーム名を変更する。参加者なら誰でも変更できる（LINE のグループと同じ）。

    変更した場合は「〇〇がトーク名を変更しました」を同じトランザクションで記録し、
    (ルーム, システムメッセージ) を返す。名前が変わらない場合は何もせず (ルーム, None)。
    """
    require_member(db, room_id, user)
    room = get_room(db, room_id)
    if room.name == name:
        return room, None
    _ensure_name_available(db, name)

    room.name = name
    notice = add_system_message(db, room_id, user, models.MessageKind.ROOM_RENAMED, content=name)
    _commit_or_conflict(db, name)
    db.refresh(notice)
    return room, notice


def _ensure_name_available(db: Session, name: str) -> None:
    if db.scalar(select(models.Room).where(models.Room.name == name)) is not None:
        raise ConflictError(f"Room '{name}' already exists")


def _commit_or_conflict(db: Session, name: str) -> None:
    """コミットする。事前チェックの後に同名ルームが同時に作られていた場合は 409 にする。"""
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise ConflictError(f"Room '{name}' already exists") from e
