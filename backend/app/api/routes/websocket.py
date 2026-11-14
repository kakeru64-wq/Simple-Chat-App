"""/ws : ログイン中のユーザーへ、参加中ルームのイベントを配信する WebSocket。

メッセージの送信・取り消しは REST に一本化し、WebSocket はサーバー → クライアントの配信専用。
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.database import SessionLocal
from app.core.errors import AppError
from app.realtime.connections import manager
from app.services import auth

router = APIRouter(tags=["websocket"])

# 4000 番台はアプリケーションが自由に定義できるクローズコード
WS_CLOSE_UNAUTHORIZED = 4401


@router.websocket("/ws")
async def user_events(websocket: WebSocket, token: str = "") -> None:
    # 認証だけ行い、DB セッションは接続中ずっと保持しない
    with SessionLocal() as db:
        try:
            user_id = auth.get_user_by_token(db, token).id
        except AppError:
            await websocket.accept()
            await websocket.close(code=WS_CLOSE_UNAUTHORIZED)
            return

    await manager.connect(user_id, websocket)
    try:
        # クライアントからの受信は使わないが、切断を検知するために待ち受ける
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(user_id, websocket)
