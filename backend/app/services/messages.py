"""メッセージの一覧・投稿（テキスト / 画像）・取り消し。いずれもルーム参加者のみ可能。"""

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models
from app.core.errors import ForbiddenError, NotFoundError
from app.services.room_access import require_member
from app.storage import images


def list_messages(
    db: Session, room_id: int, user: models.User, *, before_id: int | None, limit: int
) -> tuple[Sequence[models.Message], bool]:
    """before_id より古いメッセージを最大 limit 件、古い順で返す（カーソル型ページング）。

    戻り値の bool は「さらに古いメッセージがあるか」。
    OFFSET 方式と違い、新着が増えても取得範囲がずれない。
    取り消し済みのメッセージも「取り消しました」と表示するために含める。
    """
    require_member(db, room_id, user)

    stmt = select(models.Message).where(models.Message.room_id == room_id)
    if before_id is not None:
        stmt = stmt.where(models.Message.id < before_id)
    # limit + 1 件取得して、さらに古いものがあるかを判定する
    rows = db.scalars(stmt.order_by(models.Message.id.desc()).limit(limit + 1)).all()
    has_more = len(rows) > limit
    return list(reversed(rows[:limit])), has_more


def post_text(db: Session, room_id: int, user: models.User, content: str) -> models.Message:
    require_member(db, room_id, user)
    message = models.Message(
        room_id=room_id, user_id=user.id, kind=models.MessageKind.TEXT, content=content
    )
    return _save(db, message)


def post_image(db: Session, room_id: int, user: models.User, data: bytes) -> models.Message:
    require_member(db, room_id, user)
    filename = images.save_image(data)  # 形式・サイズが不正ならここで例外
    message = models.Message(
        room_id=room_id, user_id=user.id, kind=models.MessageKind.IMAGE, image_path=filename
    )
    try:
        return _save(db, message)
    except Exception:
        images.delete_image(filename)  # DB に保存できなければファイルも残さない
        raise


def delete_message(db: Session, room_id: int, message_id: int, user: models.User) -> models.Message:
    """自分の投稿を取り消す。履歴上の位置は残し、本文と画像は消去する（冪等）。"""
    require_member(db, room_id, user)
    message = db.get(models.Message, message_id)
    if message is None or message.room_id != room_id:
        raise NotFoundError(f"Message {message_id} not found")
    if message.kind not in models.USER_MESSAGE_KINDS:
        raise ForbiddenError("System messages cannot be deleted")
    if message.user_id != user.id:
        raise ForbiddenError("You can only delete your own messages")
    if message.deleted_at is not None:
        return message

    image_path = message.image_path
    message.deleted_at = models.utcnow()
    message.content = None
    message.image_path = None
    db.commit()
    if image_path:
        images.delete_image(image_path)
    return message


def _save(db: Session, message: models.Message) -> models.Message:
    db.add(message)
    db.commit()
    db.refresh(message)
    return message
