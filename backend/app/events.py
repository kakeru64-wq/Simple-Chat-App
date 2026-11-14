"""ルーム参加者へのリアルタイム配信。

イベントを組み立て、その時点の参加者全員への送信を BackgroundTasks に予約する。
送信はレスポンス返却後に非同期で行われ、予約した順に届く。
"""

from typing import Literal

from fastapi import BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app import models, schemas
from app.realtime import manager
from app.services import memberships as membership_service
from app.services import rooms as room_service


def _send_to_room(
    db: Session, background_tasks: BackgroundTasks, room_id: int, event: BaseModel
) -> None:
    member_ids = membership_service.list_member_ids(db, room_id)
    background_tasks.add_task(manager.send_to_users, member_ids, event.model_dump(mode="json"))


def publish_message(
    db: Session,
    background_tasks: BackgroundTasks,
    event_type: Literal["message.created", "message.deleted"],
    message: models.Message,
) -> schemas.MessageOut:
    """メッセージの作成・取り消しを配信し、レスポンス用のスキーマを返す。"""
    out = schemas.MessageOut.model_validate(message)
    event = schemas.MessageEvent(type=event_type, message=out)
    _send_to_room(db, background_tasks, message.room_id, event)
    return out


def publish_room_updated(db: Session, background_tasks: BackgroundTasks, room_id: int) -> None:
    """ルーム情報（名前・人数）の変更を配信する。"""
    event = schemas.RoomUpdatedEvent(room=room_service.get_room_ref(db, room_id))
    _send_to_room(db, background_tasks, room_id, event)
