from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Query, status

from app import schemas
from app.deps import CurrentUser, DbSession
from app.realtime import manager
from app.services import memberships as membership_service
from app.services import rooms as room_service

router = APIRouter(prefix="/api/rooms", tags=["rooms"])


@router.get("", response_model=list[schemas.RoomOut])
def list_rooms(
    db: DbSession,
    user: CurrentUser,
    q: Annotated[
        str | None,
        Query(max_length=30, description="ルーム名の部分一致検索（大小文字を区別しない）"),
    ] = None,
):
    """ルームを、参加状態・未読数・最新メッセージ付きで、最近動きのあった順に返す。"""
    return room_service.list_room_views(db, user, query=(q or "").strip() or None)


@router.post("", response_model=schemas.RoomOut, status_code=status.HTTP_201_CREATED)
def create_room(body: schemas.RoomCreate, db: DbSession, user: CurrentUser):
    """ルームを作成し、作成者はそのまま参加する。"""
    room = room_service.create_room(db, body.name, creator=user)
    return room_service.get_room_view(db, room.id, user)


@router.get("/{room_id}", response_model=schemas.RoomOut)
def get_room(room_id: int, db: DbSession, user: CurrentUser):
    return room_service.get_room_view(db, room_id, user)


@router.patch("/{room_id}", response_model=schemas.RoomOut)
def rename_room(
    room_id: int,
    body: schemas.RoomUpdate,
    db: DbSession,
    user: CurrentUser,
    background_tasks: BackgroundTasks,
):
    """ルーム名を変更する（参加者のみ。同名のルームがあれば 409）。参加者全員へ配信する。"""
    room = room_service.rename_room(db, room_id, user, body.name)
    event = schemas.RoomUpdatedEvent(room=schemas.RoomRef.model_validate(room))
    member_ids = membership_service.list_member_ids(db, room_id)
    background_tasks.add_task(manager.send_to_users, member_ids, event.model_dump(mode="json"))
    return room_service.get_room_view(db, room_id, user)


@router.put("/{room_id}/members/me", response_model=schemas.RoomOut)
def join_room(room_id: int, db: DbSession, user: CurrentUser):
    """参加する（冪等）。"""
    membership_service.join(db, room_id, user)
    return room_service.get_room_view(db, room_id, user)


@router.delete("/{room_id}/members/me", status_code=status.HTTP_204_NO_CONTENT)
def leave_room(room_id: int, db: DbSession, user: CurrentUser) -> None:
    """退会する（冪等）。退会後はメッセージの閲覧・投稿・受信ができなくなる。"""
    membership_service.leave(db, room_id, user)


@router.put("/{room_id}/read", status_code=status.HTTP_204_NO_CONTENT)
def mark_read(room_id: int, body: schemas.MarkReadRequest, db: DbSession, user: CurrentUser):
    """指定したメッセージまで既読にする。"""
    membership_service.mark_read(db, room_id, user, body.message_id)
