# pylint: disable=unused-argument
from typing import Annotated, Optional
from enum import Enum
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel, Field, field_validator
from fastapi import APIRouter, Depends, status, Path
from cinema_application.models import Movie, MovieSession, Room
from cinema_application.routers.auth import get_current_user
from cinema_application.database import get_db
from cinema_application.exceptions import (
    NotFoundException,
    MovieOrRoomNotFoundException,
    WrongParametersException,
)

router = APIRouter(prefix="/sessions", tags=["sessions"])

DbDependency = Annotated[Session, Depends(get_db)]
UserDependency = Annotated[dict, Depends(get_current_user)]


class MovieSessionRequest(BaseModel):
    start_time: str = Field(
        description="Please use '%d-%m-%Y %H:%M' format.",
        examples=["18-03-2024 12:05", "24-12-2021 21:05"],
        pattern="^\d{2}-\d{2}-\d{4} \d{2}:\d{2}$",  # pylint: disable=anomalous-backslash-in-string
    )
    end_time: str = Field(
        description="Please use '%d-%m-%Y %H:%M' format.",
        examples=["18-03-2024 12:05", "24-12-2021 21:05"],
        pattern="^\d{2}-\d{2}-\d{4} \d{2}:\d{2}$",  # pylint: disable=anomalous-backslash-in-string
    )

    movie_id: int = Field(gt=0)
    room_id: int = Field(gt=0)

    @field_validator("start_time", "end_time")
    @classmethod
    def parse_time(cls, value: str):
        return datetime.strptime(value, "%d-%m-%Y %H:%M")


class MovieSessionUpdate(BaseModel):
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    movie_id: Optional[int] = None
    room_id: Optional[int] = None


class ParentExam(str, Enum):
    MOVIE = "movie"
    ROOM = "room"


@router.get("/", status_code=status.HTTP_200_OK)
async def all_sessions(admin: UserDependency, database: DbDependency):
    return database.query(MovieSession).all()


@router.get("/{session_id}", status_code=status.HTTP_200_OK)
async def get_session_by_id(database: DbDependency, session_id: int = Path(gt=0)):
    data = (
        database.query(MovieSession)
        .options(
            joinedload(MovieSession.movie),
            joinedload(MovieSession.room),
            joinedload(MovieSession.reservations),
        )
        .filter(MovieSession.id == session_id)
        .first()
    )

    if data is None:
        raise NotFoundException

    reserved_seats = [reservation.seat for reservation in data.reservations]
    available_seats = [
        seat for seat in range(1, data.room.seats + 1) if seat not in reserved_seats
    ]
    todo_element = {
        "session": data,
        "reserved_seats": reserved_seats,
        "available_seats": available_seats,
    }
    return todo_element


@router.get("/filtered/", status_code=status.HTTP_200_OK)
# async def sessions_by(parent: ParentExam, parent_id: int, database: DbDependency):
async def sessions_filtered_by(
    database: DbDependency, movie_id: int = None, room_id: int = None
):
    if not movie_id and not room_id:
        raise WrongParametersException
    if movie_id and room_id:
        return (
            database.query(MovieSession)
            .filter(MovieSession.movie_id == movie_id, MovieSession.room_id == room_id)
            .filter(MovieSession.start_time > datetime.now())
            .all()
        )
    elif movie_id:
        return (
            database.query(MovieSession).filter(MovieSession.movie_id == movie_id).all()
        )
    elif room_id:
        return (
            database.query(MovieSession).filter(MovieSession.room_id == room_id).all()
        )


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_session(
    admin: UserDependency,
    database: DbDependency,
    session_request: MovieSessionRequest,
):
    session_params = session_request.model_dump()
    if (
        not database.query(Movie)
        .filter(Movie.id == session_params.get("movie_id"))
        .first()
        or not database.query(Room)
        .filter(Room.id == session_params.get("room_id"))
        .first()
    ):
        raise MovieOrRoomNotFoundException

    new_todo_element = MovieSession(**session_params)

    database.add(new_todo_element)
    database.commit()


@router.put("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_session(
    admin: UserDependency,
    database: DbDependency,
    session_request: MovieSessionUpdate,
    session_id: int = Path(gt=0),
):
    updatable_todo = (
        database.query(MovieSession).filter(MovieSession.id == session_id).first()
    )
    if not updatable_todo:
        raise NotFoundException

    session_params = session_request.model_dump(exclude_unset=True)
    if "movie_id" in session_params:
        if (
            not database.query(Movie)
            .filter(Movie.id == session_params.get("movie_id"))
            .first()
        ):
            raise MovieOrRoomNotFoundException
    if "room_id" in session_params:
        if (
            not database.query(Room)
            .filter(Room.id == session_params.get("room_id"))
            .first()
        ):
            raise MovieOrRoomNotFoundException

    updatable_todo.update(**session_params)

    database.add(updatable_todo)
    database.commit()


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    admin: UserDependency, database: DbDependency, session_id: int = Path(gt=0)
):
    deletable_todo = (
        database.query(MovieSession).filter(MovieSession.id == session_id).first()
    )
    if not deletable_todo:
        raise NotFoundException
    database.delete(deletable_todo)
    database.commit()
