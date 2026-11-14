"""ログイン中ユーザーへイベントを配信する WebSocket エンドポイント。

メッセージの送信・削除は REST に一本化し、WebSocket はサーバー → クライアントの
配信専用とする。参加中のルームのイベントだけが届く。
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.db import SessionLocal
from app.errors import AppError
from app.realtime import manager
from app.services import auth as auth_service

router = APIRouter(tags=["websocket"])

# 4000 番台はアプリケーション定義のクローズコード
WS_CLOSE_UNAUTHORIZED = 4401


@router.websocket("/ws")
async def user_events(websocket: WebSocket, token: str = "") -> None:
    # 認証だけ行い、DB セッションは接続中保持しない
    with SessionLocal() as db:
        try:
            user_id = auth_service.get_user_by_token(db, token).id
        except AppError:
            await websocket.accept()
            await websocket.close(code=WS_CLOSE_UNAUTHORIZED)
            return

    await manager.connect(user_id, websocket)
    try:
        # クライアントからの受信は使わないが、切断検知のために待ち受ける
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(user_id, websocket)
