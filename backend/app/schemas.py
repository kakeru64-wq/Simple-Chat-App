"""API の入出力スキーマ（Pydantic）。"""

from datetime import UTC, datetime
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PlainSerializer,
    StringConstraints,
    computed_field,
)


def _to_utc_iso(value: datetime) -> str:
    # SQLite はタイムゾーン情報を保持しないため、UTC として明示して返す
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.isoformat()


UtcDatetime = Annotated[datetime, PlainSerializer(_to_utc_iso, return_type=str)]

UserName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=20)]
RoomName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=30)]
MessageContent = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)
]


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---- Users / Auth ----
class LoginRequest(BaseModel):
    name: UserName


class UserOut(ORMModel):
    id: int
    name: str
    created_at: UtcDatetime


class LoginResponse(BaseModel):
    token: str
    user: UserOut


# ---- Messages ----
class MessageCreate(BaseModel):
    content: MessageContent


class MessageOut(ORMModel):
    id: int
    room_id: int
    user: UserOut = Field(description="投稿者（システムメッセージでは操作したユーザー）")
    kind: Literal["text", "image", "room_renamed", "member_joined", "member_left"]
    content: str | None = Field(
        description="テキスト本文（room_renamed では変更後のトーク名）。画像・削除済みは null"
    )
    image_path: str | None = Field(exclude=True)
    deleted_at: UtcDatetime | None = Field(exclude=True)
    created_at: UtcDatetime

    @computed_field(description="画像の URL（API サーバーからの相対パス）")
    @property
    def image_url(self) -> str | None:
        return f"/uploads/{self.image_path}" if self.image_path else None

    @computed_field
    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None


class MessageListResponse(BaseModel):
    messages: list[MessageOut] = Field(description="古い順に並んだメッセージ")
    has_more: bool = Field(description="さらに古いメッセージが存在するか")


# ---- Rooms ----
class RoomCreate(BaseModel):
    name: RoomName


class RoomUpdate(BaseModel):
    name: RoomName


class RoomRef(BaseModel):
    """全参加者に共通のルーム情報（ユーザーごとの未読数などを含まない）。配信用。"""

    id: int
    name: str
    member_count: int


class RoomOut(BaseModel):
    """ルーム情報に、閲覧ユーザーから見た状態（参加・未読・最新メッセージ）を加えたもの。"""

    id: int
    name: str
    created_at: UtcDatetime
    member_count: int
    is_member: bool
    unread_count: int = Field(description="未読数（自分の投稿・削除済みは除く）。未参加なら 0")
    last_message: MessageOut | None = Field(description="削除されていない最新メッセージ")


class MarkReadRequest(BaseModel):
    message_id: int = Field(ge=0, description="ここまで読んだメッセージの ID")


# ---- WebSocket events ----
class MessageEvent(BaseModel):
    type: Literal["message.created", "message.deleted"]
    message: MessageOut


class RoomUpdatedEvent(BaseModel):
    type: Literal["room.updated"] = "room.updated"
    room: RoomRef
