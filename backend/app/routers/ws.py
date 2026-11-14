"""ルームの新着メッセージを配信する WebSocket エンドポイント。

メッセージ送信は REST (POST /api/rooms/{id}/messages) に一本化し、
WebSocket はサーバー → クライアントの配信専用とする。
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.db import SessionLocal
from app.errors import AppError
from app.realtime import manager
from app.services import auth as auth_service
from app.services import rooms as room_service

router = APIRouter(tags=["websocket"])

# 4000 番台はアプリケーション定義のクローズコード
WS_CLOSE_UNAUTHORIZED = 4401
WS_CLOSE_NOT_FOUND = 4404


@router.websocket("/ws/rooms/{room_id}")
async def room_events(websocket: WebSocket, room_id: int, token: str = "") -> None:
    # 認証とルーム確認だけ行い、DB セッションは接続中保持しない
    with SessionLocal() as db:
        try:
            auth_service.get_user_by_token(db, token)
        except AppError:
            await websocket.accept()
            await websocket.close(code=WS_CLOSE_UNAUTHORIZED)
            return
        try:
            room_service.get_room(db, room_id)
        except AppError:
            await websocket.accept()
            await websocket.close(code=WS_CLOSE_NOT_FOUND)
            return

    await manager.connect(room_id, websocket)
    try:
        # クライアントからの受信は使わないが、切断検知のために待ち受ける
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(room_id, websocket)
