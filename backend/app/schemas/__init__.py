"""API の入出力と WebSocket イベントの形（Pydantic）。`from app import schemas` で使う。"""

from app.schemas.auth import LoginRequest, LoginResponse, UserOut
from app.schemas.event import MessageEvent, RoomUpdatedEvent
from app.schemas.message import MessageCreate, MessageListResponse, MessageOut
from app.schemas.room import MarkReadRequest, RoomCreate, RoomOut, RoomRef, RoomUpdate

__all__ = [
    "LoginRequest",
    "LoginResponse",
    "MarkReadRequest",
    "MessageCreate",
    "MessageEvent",
    "MessageListResponse",
    "MessageOut",
    "RoomCreate",
    "RoomOut",
    "RoomRef",
    "RoomUpdate",
    "RoomUpdatedEvent",
    "UserOut",
]
