"""WebSocket 接続の管理とルーム単位のブロードキャスト。

単一プロセス前提でメモリ上に接続を保持する。複数プロセス／複数サーバーに
スケールする場合は、broadcast を Redis Pub/Sub 等に差し替えればよい。
"""

import asyncio
import logging
from collections import defaultdict

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self) -> None:
        self._rooms: dict[int, set[WebSocket]] = defaultdict(set)

    async def connect(self, room_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self._rooms[room_id].add(websocket)

    def disconnect(self, room_id: int, websocket: WebSocket) -> None:
        connections = self._rooms.get(room_id)
        if connections is None:
            return
        connections.discard(websocket)
        if not connections:
            del self._rooms[room_id]

    async def broadcast(self, room_id: int, payload: dict) -> None:
        connections = list(self._rooms.get(room_id, ()))
        results = await asyncio.gather(
            *(ws.send_json(payload) for ws in connections), return_exceptions=True
        )
        # 送信に失敗した（切断済みの）接続は取り除く
        for ws, result in zip(connections, results, strict=True):
            if isinstance(result, Exception):
                logger.info("Dropping dead websocket in room %s: %r", room_id, result)
                self.disconnect(room_id, ws)


manager = ConnectionManager()
