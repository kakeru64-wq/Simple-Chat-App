from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, File, Query, UploadFile, status

from app import events, schemas
from app.config import get_settings
from app.deps import CurrentUser, DbSession
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
    return events.publish_message(db, background_tasks, "message.created", message)


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
    return events.publish_message(db, background_tasks, "message.created", message)


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
    return events.publish_message(db, background_tasks, "message.deleted", message)
