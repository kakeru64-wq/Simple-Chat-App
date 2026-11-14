"""API の入出力スキーマ（Pydantic）。"""

from datetime import UTC, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_serializer

UserName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=20)]
RoomName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=30)]
MessageContent = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)
]


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    @field_serializer("created_at", check_fields=False)
    def _serialize_dt(self, value: datetime) -> str:
        # SQLite はタイムゾーン情報を保持しないため、UTC として明示して返す
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value.isoformat()


# ---- Users / Auth ----
class LoginRequest(BaseModel):
    name: UserName


class UserOut(ORMModel):
    id: int
    name: str
    created_at: datetime


class LoginResponse(BaseModel):
    token: str
    user: UserOut


# ---- Rooms ----
class RoomCreate(BaseModel):
    name: RoomName


class RoomOut(ORMModel):
    id: int
    name: str
    created_at: datetime


# ---- Messages ----
class MessageCreate(BaseModel):
    content: MessageContent


class MessageOut(ORMModel):
    id: int
    room_id: int
    user: UserOut
    content: str
    created_at: datetime


class MessageListResponse(BaseModel):
    messages: list[MessageOut] = Field(description="古い順に並んだメッセージ")
    has_more: bool = Field(description="さらに古いメッセージが存在するか")


# ---- WebSocket events ----
class MessageCreatedEvent(BaseModel):
    type: Literal["message.created"] = "message.created"
    message: MessageOut
