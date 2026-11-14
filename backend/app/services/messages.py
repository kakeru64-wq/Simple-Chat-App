"""メッセージの取得・投稿（テキスト／画像）・削除。いずれもルーム参加者のみ可能。"""

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models, storage
from app.errors import ForbiddenError, NotFoundError
from app.models import utcnow
from app.services.memberships import require_member


def list_messages(
    db: Session, room_id: int, user: models.User, *, before_id: int | None, limit: int
) -> tuple[Sequence[models.Message], bool]:
    """before_id より古いメッセージを最大 limit 件、古い順で返す（カーソル型ページング）。

    OFFSET 方式と異なり、新着が増えても取得範囲がずれない。
    削除済みメッセージも「取り消し」表示のために含める。
    """
    require_member(db, room_id, user)

    stmt = select(models.Message).where(models.Message.room_id == room_id)
    if before_id is not None:
        stmt = stmt.where(models.Message.id < before_id)
    # limit + 1 件取得して「さらに古いものがあるか」を判定する
    rows = db.scalars(stmt.order_by(models.Message.id.desc()).limit(limit + 1)).all()
    has_more = len(rows) > limit
    return list(reversed(rows[:limit])), has_more


def create_text_message(
    db: Session, room_id: int, user: models.User, content: str
) -> models.Message:
    require_member(db, room_id, user)
    return _save(db, models.Message(room_id=room_id, user_id=user.id, content=content))


def create_image_message(
    db: Session, room_id: int, user: models.User, data: bytes
) -> models.Message:
    require_member(db, room_id, user)
    filename = storage.save_image(data)  # 形式・サイズ不正ならここで例外
    try:
        return _save(db, models.Message(room_id=room_id, user_id=user.id, image_path=filename))
    except Exception:
        storage.delete_image(filename)  # DB 保存に失敗したらファイルも残さない
        raise


def delete_message(db: Session, room_id: int, message_id: int, user: models.User) -> models.Message:
    """自分のメッセージを取り消す。履歴上の位置は残し、本文と画像は消去する。"""
    require_member(db, room_id, user)
    message = db.get(models.Message, message_id)
    if message is None or message.room_id != room_id:
        raise NotFoundError(f"Message {message_id} not found")
    if message.user_id != user.id:
        raise ForbiddenError("You can only delete your own messages")
    if message.deleted_at is not None:
        return message  # 冪等

    image_path = message.image_path
    message.deleted_at = utcnow()
    message.content = None
    message.image_path = None
    db.commit()
    if image_path:
        storage.delete_image(image_path)
    return message


def _save(db: Session, message: models.Message) -> models.Message:
    db.add(message)
    db.commit()
    db.refresh(message)
    return message
