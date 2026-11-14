from fastapi import APIRouter, status

from app import schemas
from app.deps import CurrentUser, DbSession
from app.services import rooms as room_service

router = APIRouter(prefix="/api/rooms", tags=["rooms"])


@router.get("", response_model=list[schemas.RoomOut])
def list_rooms(db: DbSession, _user: CurrentUser):
    return room_service.list_rooms(db)


@router.post("", response_model=schemas.RoomOut, status_code=status.HTTP_201_CREATED)
def create_room(body: schemas.RoomCreate, db: DbSession, _user: CurrentUser):
    return room_service.create_room(db, body.name)


@router.get("/{room_id}", response_model=schemas.RoomOut)
def get_room(room_id: int, db: DbSession, _user: CurrentUser):
    return room_service.get_room(db, room_id)
