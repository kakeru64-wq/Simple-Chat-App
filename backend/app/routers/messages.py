from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Query, status

from app import schemas
from app.deps import CurrentUser, DbSession
from app.realtime import manager
from app.services import messages as message_service

router = APIRouter(prefix="/api/rooms/{room_id}/messages", tags=["messages"])


@router.get("", response_model=schemas.MessageListResponse)
def list_messages(
    room_id: int,
    db: DbSession,
    _user: CurrentUser,
    before_id: Annotated[int | None, Query(description="この ID より古いものを取得")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
):
    messages, has_more = message_service.list_messages(
        db, room_id, before_id=before_id, limit=limit
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
    """メッセージを保存し、同じルームの WebSocket 購読者へ配信する。"""
    message = message_service.create_message(db, room_id, user, body.content)
    out = schemas.MessageOut.model_validate(message)
    event = schemas.MessageCreatedEvent(message=out)
    # DB 処理は同期（スレッドプール）、配信は非同期でレスポンス返却後に行う
    background_tasks.add_task(manager.broadcast, room_id, event.model_dump(mode="json"))
    return out
