"""業務ロジック。HTTP や WebSocket のことは知らず、DB を操作してドメイン例外を送出する。

依存の向き（循環させない）:
    room_access, system_messages  ←  auth, rooms, members, messages
    room_summaries は models のみに依存する（一覧表示用の読み取り専用クエリ）
"""
