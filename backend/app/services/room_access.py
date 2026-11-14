"""ルームの存在確認と参加者チェック。権限の判定はすべてここを通す。"""

from sqlalchemy.orm import Session

from app import models
from app.core.errors import ForbiddenError, NotFoundError


def get_room(db: Session, room_id: int) -> models.Room:
    """ルームを取得する。存在しなければ 404。"""
    room = db.get(models.Room, room_id)
    if room is None:
        raise NotFoundError(f"Room {room_id} not found")
    return room


def get_membership(db: Session, room_id: int, user_id: int) -> models.RoomMember | None:
    return db.get(models.RoomMember, (room_id, user_id))


def require_member(db: Session, room_id: int, user: models.User) -> models.RoomMember:
    """ルームが存在し（なければ 404）、user が参加者である（でなければ 403）ことを確認する。"""
    get_room(db, room_id)
    membership = get_membership(db, room_id, user.id)
    if membership is None:
        raise ForbiddenError("You are not a member of this room")
    return membership
