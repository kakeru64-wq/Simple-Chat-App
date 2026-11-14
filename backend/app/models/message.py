from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models._common import utcnow
from app.models.user import User


class MessageKind(StrEnum):
    """メッセージの種類。"""

    # ユーザーの投稿
    TEXT = "text"
    IMAGE = "image"
    # システムメッセージ（操作の記録）。Message.user は操作したユーザー
    ROOM_RENAMED = "room_renamed"  # content に変更後のトーク名
    MEMBER_JOINED = "member_joined"
    MEMBER_LEFT = "member_left"


# ユーザーの投稿にあたる種類。未読数の対象で、取り消しができる。
USER_MESSAGE_KINDS = (MessageKind.TEXT, MessageKind.IMAGE)


class Message(Base):
    """ルーム内のメッセージ（ユーザーの投稿とシステムメッセージ）。

    取り消しは論理削除：deleted_at を記録し、本文と画像を消去する（履歴上の位置は残る）。
    """

    __tablename__ = "messages"
    # ルーム内のメッセージを id 順にページングするための複合インデックス
    __table_args__ = (Index("ix_messages_room_id_id", "room_id", "id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    kind: Mapped[str] = mapped_column(String(20), default=MessageKind.TEXT)
    content: Mapped[str | None] = mapped_column(Text)
    image_path: Mapped[str | None] = mapped_column(String(100))  # uploads 内のファイル名
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship(lazy="joined")
