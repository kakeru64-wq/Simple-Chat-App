"""WebSocket でクライアントへ送るイベント。"""

from typing import Literal

from pydantic import BaseModel

from app.schemas.message import MessageOut
from app.schemas.room import RoomRef


class MessageEvent(BaseModel):
    """メッセージの作成・取り消し（システムメッセージの作成も含む）"""

    type: Literal["message.created", "message.deleted"]
    message: MessageOut


class RoomUpdatedEvent(BaseModel):
    """ルーム情報（名前・人数）の変更"""

    type: Literal["room.updated"] = "room.updated"
    room: RoomRef
