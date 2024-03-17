from typing import Annotated, Optional, List
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, status, Path
from cinema_application.models import Movie, MovieSession
from cinema_application.routers.auth import get_current_user
from cinema_application.database import get_db
from cinema_application.exceptions import NotFoundException

router = APIRouter(prefix="/movies", tags=["movies"])

DbDependency = Annotated[Session, Depends(get_db)]
UserDependency = Annotated[dict, Depends(get_current_user)]


class MovieRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    duration: Optional[int] = None
    poster: Optional[bytes] = None


class MovieUpdate(BaseModel):
    name: Optional[str] = None
    duration: Optional[int] = None
    poster: Optional[bytes] = None


@router.get("/", status_code=status.HTTP_200_OK)
async def all_movies(admin: UserDependency, database: DbDependency):
    return database.query(Movie).all()


@router.get("/available_movies", status_code=status.HTTP_200_OK)
async def movies_with_sessions(database: DbDependency):
    return (
        database.query(Movie)
        .join(MovieSession, MovieSession.movie_id == Movie.id)
        .distinct(Movie.id)
        .all()
    )


# @router.get("/{room_id}", status_code=status.HTTP_200_OK)
# async def get_movie_by_id(database: DbDependency, movie_id: int = Path(gt=0)):
#     todo_element = database.query(Movie).filter(Movie.id == movie_id).first()
#     if todo_element is None:
#         raise NotFoundException
#     return todo_element


@router.get("/{movie_id}", status_code=status.HTTP_200_OK)
async def get_movie_by_id(database: DbDependency, movie_id: int = Path(gt=0)):
    todo_element = database.query(Movie).filter(Movie.id == movie_id).first()
    if todo_element is None:
        raise NotFoundException
    return todo_element


@router.get("/by_room/{room_id}", status_code=status.HTTP_200_OK)
async def get_movies_by_room(database: DbDependency, room_id: int = Path(gt=0)):
    todo_element = (
        database.query(Movie)
        .join(MovieSession)
        .filter(MovieSession.room_id == room_id)
        .distinct()
        .all()
    )
    if todo_element is None:
        raise NotFoundException
    return todo_element


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_movie(
    admin: UserDependency,
    database: DbDependency,
    movie_request: MovieRequest,
):
    new_todo_element = Movie(**movie_request.model_dump(exclude_unset=True))

    database.add(new_todo_element)
    database.commit()


@router.put("/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_movie(
    admin: UserDependency,
    database: DbDependency,
    room_request: MovieUpdate,
    movie_id: int = Path(gt=0),
):
    updatable_todo = database.query(Movie).filter(Movie.id == movie_id).first()
    if not updatable_todo:
        raise NotFoundException

    updatable_todo.update(**room_request.model_dump(exclude_unset=True))

    database.add(updatable_todo)
    database.commit()


@router.delete("/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(
    admin: UserDependency, database: DbDependency, movie_id: int = Path(gt=0)
):
    deletable_todo = database.query(Movie).filter(Movie.id == movie_id).first()
    if not deletable_todo:
        raise NotFoundException
    database.delete(deletable_todo)
    database.commit()
