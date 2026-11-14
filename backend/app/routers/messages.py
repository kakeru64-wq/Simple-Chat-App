from typing import Annotated, Literal

from fastapi import APIRouter, BackgroundTasks, File, Query, UploadFile, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.config import get_settings
from app.deps import CurrentUser, DbSession
from app.realtime import manager
from app.services import memberships as membership_service
from app.services import messages as message_service

router = APIRouter(prefix="/api/rooms/{room_id}/messages", tags=["messages"])


@router.get("", response_model=schemas.MessageListResponse)
def list_messages(
    room_id: int,
    db: DbSession,
    user: CurrentUser,
    before_id: Annotated[int | None, Query(description="この ID より古いものを取得")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
):
    messages, has_more = message_service.list_messages(
        db, room_id, user, before_id=before_id, limit=limit
    )
    return {"messages": messages, "has_more": has_more}


@router.post("", response_model=schemas.MessageOut, status_code=status.HTTP_201_CREATED)
def create_message(
    room_id: int,
    body: schemas.MessageCreate,
    db: DbSession,
    user: CurrentUser,
    background_tasks: BackgroundTasks,
):
    """テキストメッセージを投稿し、ルーム参加者へ配信する。"""
    message = message_service.create_text_message(db, room_id, user, body.content)
    return _publish(db, background_tasks, "message.created", message)


@router.post("/images", response_model=schemas.MessageOut, status_code=status.HTTP_201_CREATED)
def create_image_message(
    room_id: int,
    file: Annotated[UploadFile, File(description="JPEG / PNG / GIF / WebP（5MB まで）")],
    db: DbSession,
    user: CurrentUser,
    background_tasks: BackgroundTasks,
):
    """画像メッセージを投稿し、ルーム参加者へ配信する。"""
    # 上限 + 1 バイトだけ読み、超過の判定はサービス層（storage）に任せる
    data = file.file.read(get_settings().max_image_bytes + 1)
    message = message_service.create_image_message(db, room_id, user, data)
    return _publish(db, background_tasks, "message.created", message)


@router.delete("/{message_id}", response_model=schemas.MessageOut)
def delete_message(
    room_id: int,
    message_id: int,
    db: DbSession,
    user: CurrentUser,
    background_tasks: BackgroundTasks,
):
    """自分のメッセージを取り消す。取り消し後の状態を返し、参加者へ配信する。"""
    message = message_service.delete_message(db, room_id, message_id, user)
    return _publish(db, background_tasks, "message.deleted", message)


def _publish(
    db: Session,
    background_tasks: BackgroundTasks,
    event_type: Literal["message.created", "message.deleted"],
    message: models.Message,
) -> schemas.MessageOut:
    """ルーム参加者へイベントを配信する。配信はレスポンス返却後に非同期で行う。"""
    out = schemas.MessageOut.model_validate(message)
    event = schemas.MessageEvent(type=event_type, message=out)
    member_ids = membership_service.list_member_ids(db, message.room_id)
    background_tasks.add_task(manager.send_to_users, member_ids, event.model_dump(mode="json"))
    return out
