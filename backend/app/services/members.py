"""ルームへの参加・退会と既読位置の管理。"""

from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import models
from app.services.room_access import get_membership, get_room, require_member
from app.services.system_messages import add_system_message


def join(db: Session, room_id: int, user: models.User) -> models.Message | None:
    """参加し、「〇〇が参加しました」を記録して返す。参加済みなら何もせず None（冪等）。

    参加前の履歴は未読として数えないよう、既読位置を現在の最新メッセージに合わせる。
    """
    get_room(db, room_id)
    if get_membership(db, room_id, user.id) is not None:
        return None
    db.add(
        models.RoomMember(
            room_id=room_id,
            user_id=user.id,
            last_read_message_id=_latest_message_id(db, room_id),
        )
    )
    notice = add_system_message(db, room_id, user, models.MessageKind.MEMBER_JOINED)
    db.commit()
    db.refresh(notice)
    return notice


def leave(db: Session, room_id: int, user: models.User) -> models.Message | None:
    """退会し、「〇〇が退会しました」を記録して返す。未参加なら何もせず None（冪等）。"""
    get_room(db, room_id)
    membership = get_membership(db, room_id, user.id)
    if membership is None:
        return None
    db.delete(membership)
    notice = add_system_message(db, room_id, user, models.MessageKind.MEMBER_LEFT)
    db.commit()
    db.refresh(notice)
    return notice


def mark_read(db: Session, room_id: int, user: models.User, message_id: int) -> None:
    """既読位置を message_id まで進める（後退はしない）。"""
    membership = require_member(db, room_id, user)
    target = min(message_id, _latest_message_id(db, room_id))
    if target > membership.last_read_message_id:
        membership.last_read_message_id = target
        db.commit()


def list_member_ids(db: Session, room_id: int) -> Sequence[int]:
    stmt = select(models.RoomMember.user_id).where(models.RoomMember.room_id == room_id)
    return db.scalars(stmt).all()


def _latest_message_id(db: Session, room_id: int) -> int:
    stmt = select(func.max(models.Message.id)).where(models.Message.room_id == room_id)
    return db.scalar(stmt) or 0
