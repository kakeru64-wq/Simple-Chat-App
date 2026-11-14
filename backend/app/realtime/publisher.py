"""ルーム参加者へのイベント配信。

イベントを組み立て、その時点の参加者全員への送信を BackgroundTasks に予約する。
送信はレスポンスを返した後に非同期で行われ、予約した順に届く。
"""

from typing import Literal

from fastapi import BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app import models, schemas
from app.realtime.connections import manager
from app.services import members, room_summaries


def publish_message(
    db: Session,
    background_tasks: BackgroundTasks,
    event_type: Literal["message.created", "message.deleted"],
    message: models.Message,
) -> schemas.MessageOut:
    """メッセージの作成・取り消しを配信し、レスポンス用のスキーマを返す。"""
    out = schemas.MessageOut.model_validate(message)
    _send_to_room(
        db, background_tasks, message.room_id, schemas.MessageEvent(type=event_type, message=out)
    )
    return out


def publish_room_change(
    db: Session, background_tasks: BackgroundTasks, room_id: int, notice: models.Message | None
) -> None:
    """名前変更・参加・退会の後に呼ぶ。システムメッセージと、ルーム情報（名前・人数）の変更を配信する。

    notice が None（状態が変わらなかった）なら何もしない。
    """
    if notice is None:
        return
    room = room_summaries.get_room_ref(db, room_id)
    _send_to_room(db, background_tasks, room_id, schemas.RoomUpdatedEvent(room=room))
    publish_message(db, background_tasks, "message.created", notice)


def _send_to_room(
    db: Session, background_tasks: BackgroundTasks, room_id: int, event: BaseModel
) -> None:
    member_ids = members.list_member_ids(db, room_id)
    background_tasks.add_task(manager.send_to_users, member_ids, event.model_dump(mode="json"))
