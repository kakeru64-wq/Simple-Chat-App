"""メッセージの投稿・取得。"""

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models
from app.services.rooms import get_room


def list_messages(
    db: Session, room_id: int, *, before_id: int | None, limit: int
) -> tuple[Sequence[models.Message], bool]:
    """before_id より古いメッセージを最大 limit 件、古い順で返す（カーソル型ページング）。

    OFFSET 方式と異なり、新着が増えても取得範囲がずれない。
    """
    get_room(db, room_id)  # ルームの存在確認（なければ 404）

    stmt = select(models.Message).where(models.Message.room_id == room_id)
    if before_id is not None:
        stmt = stmt.where(models.Message.id < before_id)
    # limit + 1 件取得して「さらに古いものがあるか」を判定する
    rows = db.scalars(stmt.order_by(models.Message.id.desc()).limit(limit + 1)).all()
    has_more = len(rows) > limit
    return list(reversed(rows[:limit])), has_more


def create_message(db: Session, room_id: int, user: models.User, content: str) -> models.Message:
    get_room(db, room_id)
    message = models.Message(room_id=room_id, user_id=user.id, content=content)
    db.add(message)
    db.commit()
    db.refresh(message)
    return message
