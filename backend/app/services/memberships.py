"""ルームへの参加・退会と既読位置の管理。"""

from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import models
from app.errors import ForbiddenError
from app.services.rooms import get_room


def get_membership(db: Session, room_id: int, user_id: int) -> models.RoomMember | None:
    return db.get(models.RoomMember, (room_id, user_id))


def require_member(db: Session, room_id: int, user: models.User) -> models.RoomMember:
    """ルームの存在（なければ 404）と参加状態（未参加なら 403）を確認する。"""
    get_room(db, room_id)
    membership = get_membership(db, room_id, user.id)
    if membership is None:
        raise ForbiddenError("You are not a member of this room")
    return membership


def _latest_message_id(db: Session, room_id: int) -> int:
    stmt = select(func.max(models.Message.id)).where(models.Message.room_id == room_id)
    return db.scalar(stmt) or 0


def add_member(db: Session, room_id: int, user_id: int) -> None:
    """参加レコードを追加する（コミットは呼び出し側）。参加前の履歴は未読として数えない。"""
    db.add(
        models.RoomMember(
            room_id=room_id,
            user_id=user_id,
            last_read_message_id=_latest_message_id(db, room_id),
        )
    )


def join(db: Session, room_id: int, user: models.User) -> models.Message | None:
    """参加し、「〇〇が参加しました」のシステムメッセージを記録して返す。

    参加済みなら何もせず None を返す（冪等）。
    """
    get_room(db, room_id)
    if get_membership(db, room_id, user.id) is not None:
        return None
    add_member(db, room_id, user.id)
    return _record(db, room_id, user, models.MessageKind.MEMBER_JOINED)


def leave(db: Session, room_id: int, user: models.User) -> models.Message | None:
    """退会し、「〇〇が退会しました」のシステムメッセージを記録して返す。

    未参加なら何もせず None を返す（冪等）。
    """
    get_room(db, room_id)
    membership = get_membership(db, room_id, user.id)
    if membership is None:
        return None
    db.delete(membership)
    return _record(db, room_id, user, models.MessageKind.MEMBER_LEFT)


def _record(
    db: Session, room_id: int, user: models.User, kind: models.MessageKind
) -> models.Message:
    """参加状態の変更とシステムメッセージを同じトランザクションで保存する。"""
    notice = models.Message(room_id=room_id, user_id=user.id, kind=kind)
    db.add(notice)
    db.commit()
    db.refresh(notice)
    return notice


def list_member_ids(db: Session, room_id: int) -> Sequence[int]:
    stmt = select(models.RoomMember.user_id).where(models.RoomMember.room_id == room_id)
    return db.scalars(stmt).all()


def mark_read(db: Session, room_id: int, user: models.User, message_id: int) -> None:
    """既読位置を進める（戻すことはしない）。"""
    membership = require_member(db, room_id, user)
    target = min(message_id, _latest_message_id(db, room_id))
    if target > membership.last_read_message_id:
        membership.last_read_message_id = target
        db.commit()
