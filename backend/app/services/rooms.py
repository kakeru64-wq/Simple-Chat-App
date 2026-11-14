"""ルームの作成・取得と、一覧表示用の集計（参加状態・未読数・最新メッセージ）。"""

from collections.abc import Sequence

from sqlalchemy import and_, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models, schemas
from app.errors import ConflictError, ForbiddenError, NotFoundError


def get_room(db: Session, room_id: int) -> models.Room:
    room = db.get(models.Room, room_id)
    if room is None:
        raise NotFoundError(f"Room {room_id} not found")
    return room


def find_room_by_name(db: Session, name: str) -> models.Room | None:
    return db.scalar(select(models.Room).where(models.Room.name == name))


def create_room(db: Session, name: str, creator: models.User | None = None) -> models.Room:
    """ルームを作成する。作成者を指定した場合はそのまま参加させる。"""
    if find_room_by_name(db, name) is not None:
        raise ConflictError(f"Room '{name}' already exists")
    room = models.Room(name=name)
    db.add(room)
    try:
        db.flush()
        if creator is not None:
            db.add(models.RoomMember(room_id=room.id, user_id=creator.id))
        db.commit()
    except IntegrityError as e:  # 事前チェック後に同名ルームが同時作成された場合
        db.rollback()
        raise ConflictError(f"Room '{name}' already exists") from e
    return room


def rename_room(
    db: Session, room_id: int, user: models.User, name: str
) -> tuple[models.Room, models.Message | None]:
    """ルーム名を変更する。参加者なら誰でも変更できる（LINE のグループと同じ）。

    変更した場合は「〇〇がトーク名を変更しました」のシステムメッセージを同じトランザクションで
    記録し、(ルーム, システムメッセージ) を返す。名前が同じなら何もせずメッセージは None。
    """
    room = get_room(db, room_id)
    if db.get(models.RoomMember, (room_id, user.id)) is None:
        raise ForbiddenError("You are not a member of this room")
    if room.name == name:
        return room, None
    if find_room_by_name(db, name) is not None:
        raise ConflictError(f"Room '{name}' already exists")

    room.name = name
    notice = models.Message(
        room_id=room_id, user_id=user.id, kind=models.MessageKind.ROOM_RENAMED, content=name
    )
    db.add(notice)
    try:
        db.commit()
    except IntegrityError as e:  # 事前チェック後に同名ルームが同時に作られた場合
        db.rollback()
        raise ConflictError(f"Room '{name}' already exists") from e
    db.refresh(notice)
    return room, notice


def list_room_views(
    db: Session, user: models.User, *, query: str | None = None
) -> list[schemas.RoomOut]:
    """ルームを、閲覧ユーザーから見た状態付きで、最近動きのあった順に返す。

    query を指定すると、ルーム名の部分一致（大文字小文字を区別しない）で絞り込む。
    """
    stmt = select(models.Room)
    if query:
        stmt = stmt.where(models.Room.name.ilike(f"%{_escape_like(query)}%", escape=_LIKE_ESCAPE))
    rooms = db.scalars(stmt).all()
    views = _build_views(db, rooms, user)
    return sorted(
        views,
        key=lambda v: (v.last_message.id if v.last_message else 0, v.id),
        reverse=True,
    )


_LIKE_ESCAPE = "\\"


def _escape_like(text: str) -> str:
    """LIKE のワイルドカード（% と _）を通常の文字として扱うためにエスケープする。"""
    for char in (_LIKE_ESCAPE, "%", "_"):  # エスケープ文字自体を最初に処理する
        text = text.replace(char, _LIKE_ESCAPE + char)
    return text


def get_room_view(db: Session, room_id: int, user: models.User) -> schemas.RoomOut:
    return _build_views(db, [get_room(db, room_id)], user)[0]


def _build_views(
    db: Session, rooms: Sequence[models.Room], user: models.User
) -> list[schemas.RoomOut]:
    """N+1 にならないよう、集計はルーム横断の GROUP BY でまとめて取得する。"""
    room_ids = [r.id for r in rooms]
    if not room_ids:
        return []
    M, RM = models.Message, models.RoomMember

    member_counts = dict(
        db.execute(
            select(RM.room_id, func.count()).where(RM.room_id.in_(room_ids)).group_by(RM.room_id)
        ).all()
    )
    my_room_ids = set(
        db.scalars(select(RM.room_id).where(RM.user_id == user.id, RM.room_id.in_(room_ids)))
    )
    latest_ids = (
        select(func.max(M.id))
        .where(M.room_id.in_(room_ids), M.deleted_at.is_(None))
        .group_by(M.room_id)
    )
    last_messages = {m.room_id: m for m in db.scalars(select(M).where(M.id.in_(latest_ids)))}
    unread_counts = dict(
        db.execute(
            select(M.room_id, func.count())
            .join(RM, and_(RM.room_id == M.room_id, RM.user_id == user.id))
            .where(
                M.room_id.in_(room_ids),
                M.id > RM.last_read_message_id,
                M.user_id != user.id,
                M.deleted_at.is_(None),
                M.kind.in_(models.USER_MESSAGE_KINDS),  # システムメッセージは未読に数えない
            )
            .group_by(M.room_id)
        ).all()
    )

    return [
        schemas.RoomOut(
            id=room.id,
            name=room.name,
            created_at=room.created_at,
            member_count=member_counts.get(room.id, 0),
            is_member=room.id in my_room_ids,
            unread_count=unread_counts.get(room.id, 0),
            last_message=(
                schemas.MessageOut.model_validate(last_messages[room.id])
                if room.id in last_messages
                else None
            ),
        )
        for room in rooms
    ]
