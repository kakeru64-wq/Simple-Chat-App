"""WebSocket 接続の管理と、ユーザー単位の配信。

接続はルームごとではなくユーザーごとに 1 本（タブごと）にしている。
サーバーはイベントを「ルームの参加者全員」に送るため、クライアントはルーム一覧
（未読数・最新メッセージ）とチャット画面の両方を同じ接続で更新できる。

単一プロセス前提でメモリ上に接続を保持する。複数プロセス／複数サーバーに
スケールする場合は、send_to_users を Redis Pub/Sub 等に差し替えればよい。
"""

import asyncio
import logging
from collections import defaultdict
from collections.abc import Iterable

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self) -> None:
        self._users: dict[int, set[WebSocket]] = defaultdict(set)

    async def connect(self, user_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self._users[user_id].add(websocket)

    def disconnect(self, user_id: int, websocket: WebSocket) -> None:
        connections = self._users.get(user_id)
        if connections is None:
            return
        connections.discard(websocket)
        if not connections:
            del self._users[user_id]

    async def send_to_users(self, user_ids: Iterable[int], payload: dict) -> None:
        targets = [(uid, ws) for uid in set(user_ids) for ws in list(self._users.get(uid, ()))]
        results = await asyncio.gather(
            *(ws.send_json(payload) for _, ws in targets), return_exceptions=True
        )
        # 送信に失敗した（切断済みの）接続は取り除く
        for (uid, ws), result in zip(targets, results, strict=True):
            if isinstance(result, Exception):
                logger.info("Dropping dead websocket of user %s: %r", uid, result)
                self.disconnect(uid, ws)


manager = ConnectionManager()
