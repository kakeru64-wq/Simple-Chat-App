"""/api/rooms/{room_id}/messages : メッセージの一覧・投稿（テキスト / 画像）・取り消し"""

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, File, Query, UploadFile, status

from app import schemas
from app.api.deps import CurrentUser, DbSession
from app.core.config import get_settings
from app.realtime import publisher
from app.services import messages

router = APIRouter(prefix="/api/rooms/{room_id}/messages", tags=["messages"])


@router.get("", response_model=schemas.MessageListResponse)
def list_messages(
    room_id: int,
    db: DbSession,
    user: CurrentUser,
    before_id: Annotated[int | None, Query(description="この ID より古いものを取得")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
):
    items, has_more = messages.list_messages(db, room_id, user, before_id=before_id, limit=limit)
    return {"messages": items, "has_more": has_more}


@router.post("", response_model=schemas.MessageOut, status_code=status.HTTP_201_CREATED)
def post_text(
    room_id: int,
    body: schemas.MessageCreate,
    db: DbSession,
    user: CurrentUser,
    background_tasks: BackgroundTasks,
):
    """テキストを投稿し、参加者へ配信する。"""
    message = messages.post_text(db, room_id, user, body.content)
    return publisher.publish_message(db, background_tasks, "message.created", message)


@router.post("/images", response_model=schemas.MessageOut, status_code=status.HTTP_201_CREATED)
def post_image(
    room_id: int,
    file: Annotated[UploadFile, File(description="JPEG / PNG / GIF / WebP（5MB まで）")],
    db: DbSession,
    user: CurrentUser,
    background_tasks: BackgroundTasks,
):
    """画像を投稿し、参加者へ配信する。"""
    # 上限 + 1 バイトだけ読み、サイズ超過の判定は storage に任せる
    data = file.file.read(get_settings().max_image_bytes + 1)
    message = messages.post_image(db, room_id, user, data)
    return publisher.publish_message(db, background_tasks, "message.created", message)


@router.delete("/{message_id}", response_model=schemas.MessageOut)
def delete_message(
    room_id: int,
    message_id: int,
    db: DbSession,
    user: CurrentUser,
    background_tasks: BackgroundTasks,
):
    """自分の投稿を取り消す。取り消し後の状態を返し、参加者へ配信する。"""
    message = messages.delete_message(db, room_id, message_id, user)
    return publisher.publish_message(db, background_tasks, "message.deleted", message)
