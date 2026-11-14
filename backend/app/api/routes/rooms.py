"""/api/rooms : ルームの一覧（検索）・作成・取得・名前変更"""

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Query, status

from app import schemas
from app.api.deps import CurrentUser, DbSession
from app.realtime import publisher
from app.services import room_summaries, rooms

router = APIRouter(prefix="/api/rooms", tags=["rooms"])

SearchQuery = Annotated[
    str | None,
    Query(max_length=30, description="ルーム名の部分一致検索（大文字小文字を区別しない）"),
]


@router.get("", response_model=list[schemas.RoomOut])
def list_rooms(db: DbSession, user: CurrentUser, q: SearchQuery = None):
    """ルームを、参加状態・人数・未読数・最新メッセージ付きで、最近動きのあった順に返す。"""
    query = (q or "").strip() or None
    return room_summaries.list_room_summaries(db, user, query=query)


@router.post("", response_model=schemas.RoomOut, status_code=status.HTTP_201_CREATED)
def create_room(body: schemas.RoomCreate, db: DbSession, user: CurrentUser):
    """ルームを作成する。作成者はそのまま参加する（同名のルームがあれば 409）。"""
    room = rooms.create_room(db, body.name, creator=user)
    return room_summaries.get_room_summary(db, room.id, user)


@router.get("/{room_id}", response_model=schemas.RoomOut)
def get_room(room_id: int, db: DbSession, user: CurrentUser):
    return room_summaries.get_room_summary(db, room_id, user)


@router.patch("/{room_id}", response_model=schemas.RoomOut)
def rename_room(
    room_id: int,
    body: schemas.RoomUpdate,
    db: DbSession,
    user: CurrentUser,
    background_tasks: BackgroundTasks,
):
    """ルーム名を変更する（参加者のみ。同名のルームがあれば 409）。参加者全員へ配信する。"""
    _room, notice = rooms.rename_room(db, room_id, user, body.name)
    publisher.publish_room_change(db, background_tasks, room_id, notice)
    return room_summaries.get_room_summary(db, room_id, user)
