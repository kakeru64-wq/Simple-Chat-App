from typing import Literal

from pydantic import BaseModel, Field, computed_field

from app.schemas._common import MessageContent, ORMModel, UtcDatetime
from app.schemas.auth import UserOut


class MessageCreate(BaseModel):
    content: MessageContent


class MessageOut(ORMModel):
    id: int
    room_id: int
    user: UserOut = Field(description="投稿者（システムメッセージでは操作したユーザー）")
    kind: Literal["text", "image", "room_renamed", "member_joined", "member_left"]
    content: str | None = Field(
        description="テキスト本文（room_renamed では変更後のトーク名）。画像・取り消し済みは null"
    )
    created_at: UtcDatetime
    # DB の値はそのまま返さず、下の image_url / is_deleted に変換して返す
    image_path: str | None = Field(exclude=True)
    deleted_at: UtcDatetime | None = Field(exclude=True)

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
