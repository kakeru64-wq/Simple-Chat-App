"""/api/rooms/{room_id}/members/me, /read : 参加・退会・既読"""

from fastapi import APIRouter, BackgroundTasks, status

from app import schemas
from app.api.deps import CurrentUser, DbSession
from app.realtime import publisher
from app.services import members, room_summaries

router = APIRouter(prefix="/api/rooms/{room_id}", tags=["members"])


@router.put("/members/me", response_model=schemas.RoomOut)
def join_room(room_id: int, db: DbSession, user: CurrentUser, background_tasks: BackgroundTasks):
    """参加する（冪等）。参加者全員へ「参加しました」と人数の変更を配信する。"""
    notice = members.join(db, room_id, user)
    publisher.publish_room_change(db, background_tasks, room_id, notice)
    return room_summaries.get_room_summary(db, room_id, user)


@router.delete("/members/me", status_code=status.HTTP_204_NO_CONTENT)
def leave_room(
    room_id: int, db: DbSession, user: CurrentUser, background_tasks: BackgroundTasks
) -> None:
    """退会する（冪等）。以後このルームのメッセージは閲覧・投稿・受信できない。

    残った参加者へ「退会しました」と人数の変更を配信する。
    """
    notice = members.leave(db, room_id, user)
    publisher.publish_room_change(db, background_tasks, room_id, notice)


@router.put("/read", status_code=status.HTTP_204_NO_CONTENT)
def mark_read(room_id: int, body: schemas.MarkReadRequest, db: DbSession, user: CurrentUser):
    """指定したメッセージまで既読にする（後退はしない）。"""
    members.mark_read(db, room_id, user, body.message_id)
