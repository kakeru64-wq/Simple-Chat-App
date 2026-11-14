from pydantic import BaseModel, Field

from app.schemas._common import RoomName, UtcDatetime
from app.schemas.message import MessageOut


class RoomCreate(BaseModel):
    name: RoomName


class RoomUpdate(BaseModel):
    name: RoomName


class RoomOut(BaseModel):
    """ルーム情報に、閲覧ユーザーから見た状態（参加・未読・最新メッセージ）を加えたもの。"""

    id: int
    name: str
    created_at: UtcDatetime
    member_count: int
    is_member: bool
    unread_count: int = Field(description="未読数（自分の投稿・取り消し済み・システムは除く）")
    last_message: MessageOut | None = Field(description="取り消されていない最新メッセージ")


class RoomRef(BaseModel):
    """全参加者に共通のルーム情報（ユーザーごとの未読数などは含まない）。配信用。"""

    id: int
    name: str
    member_count: int


class MarkReadRequest(BaseModel):
    message_id: int = Field(ge=0, description="ここまで読んだメッセージの ID")
