"""トーク一覧・チャット画面のヘッダー用に、ルームの状態を集計する（読み取り専用）。

- RoomOut : 閲覧ユーザーから見た状態（参加しているか・未読数・最新メッセージ・人数）
- RoomRef : 全参加者に共通の情報（名前・人数）。リアルタイム配信用
"""

from collections.abc import Sequence

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app import models, schemas
from app.services.room_access import get_room

_LIKE_ESCAPE = "\\"


def list_room_summaries(
    db: Session, user: models.User, *, query: str | None = None
) -> list[schemas.RoomOut]:
    """ルームを、最近動きのあった順に返す。query を指定するとルーム名の部分一致で絞り込む。"""
    stmt = select(models.Room)
    if query:
        pattern = f"%{_escape_like(query)}%"
        stmt = stmt.where(models.Room.name.ilike(pattern, escape=_LIKE_ESCAPE))
    summaries = _summarize(db, db.scalars(stmt).all(), user)
    return sorted(
        summaries,
        key=lambda r: (r.last_message.id if r.last_message else 0, r.id),
        reverse=True,
    )


def get_room_summary(db: Session, room_id: int, user: models.User) -> schemas.RoomOut:
    return _summarize(db, [get_room(db, room_id)], user)[0]


def get_room_ref(db: Session, room_id: int) -> schemas.RoomRef:
    room = get_room(db, room_id)
    member_count = db.scalar(
        select(func.count())
        .select_from(models.RoomMember)
        .where(models.RoomMember.room_id == room_id)
    )
    return schemas.RoomRef(id=room.id, name=room.name, member_count=member_count or 0)


def _summarize(
    db: Session, rooms: Sequence[models.Room], user: models.User
) -> list[schemas.RoomOut]:
    """N+1 クエリにならないよう、集計はルーム横断の GROUP BY でまとめて取得する。"""
    room_ids = [room.id for room in rooms]
    if not room_ids:
        return []

    member_counts = _member_counts(db, room_ids)
    joined_room_ids = _joined_room_ids(db, room_ids, user)
    last_messages = _last_messages(db, room_ids)
    unread_counts = _unread_counts(db, room_ids, user)

    return [
        schemas.RoomOut(
            id=room.id,
            name=room.name,
            created_at=room.created_at,
            member_count=member_counts.get(room.id, 0),
            is_member=room.id in joined_room_ids,
            unread_count=unread_counts.get(room.id, 0),
            last_message=(
                schemas.MessageOut.model_validate(last_messages[room.id])
                if room.id in last_messages
                else None
            ),
        )
        for room in rooms
    ]


def _member_counts(db: Session, room_ids: list[int]) -> dict[int, int]:
    RM = models.RoomMember
    stmt = select(RM.room_id, func.count()).where(RM.room_id.in_(room_ids)).group_by(RM.room_id)
    return dict(db.execute(stmt).all())


def _joined_room_ids(db: Session, room_ids: list[int], user: models.User) -> set[int]:
    RM = models.RoomMember
    stmt = select(RM.room_id).where(RM.user_id == user.id, RM.room_id.in_(room_ids))
    return set(db.scalars(stmt))


def _last_messages(db: Session, room_ids: list[int]) -> dict[int, models.Message]:
    """各ルームの、取り消されていない最新メッセージ（システムメッセージを含む）。"""
    M = models.Message
    latest_ids = (
        select(func.max(M.id))
        .where(M.room_id.in_(room_ids), M.deleted_at.is_(None))
        .group_by(M.room_id)
    )
    return {m.room_id: m for m in db.scalars(select(M).where(M.id.in_(latest_ids)))}


def _unread_counts(db: Session, room_ids: list[int], user: models.User) -> dict[int, int]:
    """既読位置より新しい「他人の投稿」の数。取り消し済み・システムメッセージは数えない。"""
    M, RM = models.Message, models.RoomMember
    stmt = (
        select(M.room_id, func.count())
        .join(RM, and_(RM.room_id == M.room_id, RM.user_id == user.id))
        .where(
            M.room_id.in_(room_ids),
            M.id > RM.last_read_message_id,
            M.user_id != user.id,
            M.deleted_at.is_(None),
            M.kind.in_(models.USER_MESSAGE_KINDS),
        )
        .group_by(M.room_id)
    )
    return dict(db.execute(stmt).all())


def _escape_like(text: str) -> str:
    """LIKE のワイルドカード（% と _）を通常の文字として扱うためにエスケープする。"""
    for char in (_LIKE_ESCAPE, "%", "_"):  # エスケープ文字自体を最初に処理する
        text = text.replace(char, _LIKE_ESCAPE + char)
    return text
