from typing import Annotated, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, field_validator
from fastapi import APIRouter, Depends, status, Path
from cinema_application.models import Movie, MovieSession, Room
from cinema_application.routers.auth import get_current_user
from cinema_application.database import get_db
from cinema_application.exceptions import (
    NotFoundException,
    MovieOrRoomNotFoundException,
)

router = APIRouter(prefix="/sessions", tags=["sessions"])

DbDependency = Annotated[Session, Depends(get_db)]
UserDependency = Annotated[dict, Depends(get_current_user)]


class MovieSessionRequest(BaseModel):
    start_time: str = Field(
        description="Please use '%d-%m-%Y %H:%M' format.",
        examples=["18-03-2024 12:05", "24-12-2021 21:05"],
    )
    end_time: str = Field(
        description="Please use '%d-%m-%Y %H:%M' format.",
        examples=["18-03-2024 12:05", "24-12-2021 21:05"],
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


@router.get("/", status_code=status.HTTP_200_OK)
async def all_sessions(admin: UserDependency, database: DbDependency):
    return database.query(MovieSession).all()


@router.get("/upcoming", status_code=status.HTTP_200_OK)
async def upcoming_sessions(database: DbDependency):
    return (
        database.query(MovieSession)
        .filter(MovieSession.start_time > datetime.now())
        .all()
    )


@router.get("/{session_id}", status_code=status.HTTP_200_OK)
async def get_session_by_id(database: DbDependency, session_id: int = Path(gt=0)):
    todo_element = (
        database.query(MovieSession).filter(MovieSession.id == session_id).first()
    )
    if todo_element is None:
        raise NotFoundException
    return todo_element


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
