"""SQLAlchemy モデル（テーブル定義）。"""

from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(20), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Session(Base):
    """ログインセッション。トークンを発行し、以降のリクエストはこれで本人確認する。"""

    __tablename__ = "sessions"

    token: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped[User] = relationship()


class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class RoomMember(Base):
    """ルームの参加者。既読位置もここで管理する（未読数 = これより新しい他人のメッセージ数）。"""

    __tablename__ = "room_members"

    room_id: Mapped[int] = mapped_column(
        ForeignKey("rooms.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, index=True
    )
    last_read_message_id: Mapped[int] = mapped_column(default=0)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class MessageKind(StrEnum):
    TEXT = "text"
    IMAGE = "image"
    # 以下はシステムメッセージ（操作の記録）。user_id は操作したユーザー
    ROOM_RENAMED = "room_renamed"  # content に変更後のトーク名


# ユーザーが投稿したメッセージの種類（未読数の対象・取り消し可能）
USER_MESSAGE_KINDS = (MessageKind.TEXT, MessageKind.IMAGE)


class Message(Base):
    """メッセージ。テキスト・画像のほか、トーク名変更などのシステムメッセージも含む。

    削除は論理削除（deleted_at）で、本文と画像は消去する。
    """

    __tablename__ = "messages"
    # ルーム内のメッセージを id 順にページングするための複合インデックス
    __table_args__ = (Index("ix_messages_room_id_id", "room_id", "id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    kind: Mapped[str] = mapped_column(String(20), default=MessageKind.TEXT)
    content: Mapped[str | None] = mapped_column(Text)
    # uploads ディレクトリ内のファイル名
    image_path: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship(lazy="joined")
