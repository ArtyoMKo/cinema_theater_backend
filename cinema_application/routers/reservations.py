from typing import Annotated, Optional
from enum import Enum
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, status, Path
from cinema_application.models import Movie, MovieSession, Room, Reservation
from cinema_application.routers.auth import get_current_user
from cinema_application.database import get_db
from cinema_application.exceptions import (
    NotFoundException,
    MovieSessionNotFoundException,
)


router = APIRouter(prefix="/reservations", tags=["reservations"])

DbDependency = Annotated[Session, Depends(get_db)]
UserDependency = Annotated[dict, Depends(get_current_user)]


class ReservationRequest(BaseModel):
    seat: int = Field(gt=0, lt=1500)
    session_id: int = Field(gt=0)
    contact: str = Field()


class ReservationUpdate(BaseModel):
    seat: Optional[int] = None
    session_id: Optional[int] = None
    contact: Optional[str] = None


class ParentExam(str, Enum):
    movie = "movie"
    room = "room"


@router.get("/", status_code=status.HTTP_200_OK)
async def all_reservations(admin: UserDependency, database: DbDependency):
    return database.query(Reservation).all()


@router.get("/reservations/session_id={session_id}", status_code=status.HTTP_200_OK)
async def session_reservations(session_id: int, database: DbDependency):
    return (
        database.query(Reservation)
        .join(MovieSession)
        .filter(MovieSession.id == session_id)
        .all()
    )


@router.get(
    "/reservations/session_id={session_id}/seats", status_code=status.HTTP_200_OK
)
async def session_reservations(session_id: int, database: DbDependency):
    result = (
        database.query(Reservation)
        .join(MovieSession, Reservation.session_id == MovieSession.id)
        .filter(MovieSession.id == session_id)
        .all()
    )
    return result


@router.get("/{parent}={parent_id}", status_code=status.HTTP_200_OK)
async def reservations_by(parent: ParentExam, parent_id: int, database: DbDependency):
    parent_object = Movie if parent == ParentExam.movie else Room
    if parent == ParentExam.movie:
        return (
            database.query(Reservation)
            .join(MovieSession)
            .join(parent_object)
            .filter(parent_object.id == parent_id)
            .all()
        )


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_reservation(
    admin: UserDependency,
    database: DbDependency,
    reservation_request: ReservationRequest,
):
    reservation_params = reservation_request.model_dump()

    if (
        not database.query(MovieSession)
        .filter(MovieSession.id == reservation_params.get("session_id"))
        .first()
    ):
        raise MovieSessionNotFoundException

    new_todo_element = Reservation(**reservation_params)

    database.add(new_todo_element)
    database.commit()


@router.put("/{reservation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_reservation(
    admin: UserDependency,
    database: DbDependency,
    reservation_request: ReservationUpdate,
    reservation_id: int = Path(gt=0),
):
    updatable_todo = (
        database.query(Reservation).filter(Reservation.id == reservation_id).first()
    )

    if not updatable_todo:
        raise NotFoundException

    if (
        not database.query(MovieSession)
        .filter(MovieSession.id == updatable_todo.session_id)
        .first()
    ):
        raise MovieSessionNotFoundException

    reservation_params = reservation_request.model_dump(exclude_unset=True)

    updatable_todo.update(**reservation_params)

    database.add(updatable_todo)
    database.commit()


@router.delete("/{reservation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reservation(
    admin: UserDependency, database: DbDependency, reservation_id: int = Path(gt=0)
):
    deletable_todo = (
        database.query(Reservation).filter(Reservation.id == reservation_id).first()
    )
    if not deletable_todo:
        raise NotFoundException
    database.delete(deletable_todo)
    database.commit()
