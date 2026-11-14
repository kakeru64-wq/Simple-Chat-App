"""システムメッセージ（「〇〇が参加しました」など、操作の記録）の作成。

表示文は保存せず、種類・操作者・値（変更後のトーク名など）だけを記録する。
文言はフロントエンドで組み立てる。
"""

from sqlalchemy.orm import Session

from app import models


def add_system_message(
    db: Session,
    room_id: int,
    actor: models.User,
    kind: models.MessageKind,
    content: str | None = None,
) -> models.Message:
    """システムメッセージをセッションに追加する。

    コミットは呼び出し側で行い、元の操作（参加・退会・名前変更）と同じトランザクションで保存する。
    """
    message = models.Message(room_id=room_id, user_id=actor.id, kind=kind, content=content)
    db.add(message)
    return message
