# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from cinema_application.database import Base
from cinema_application.database import get_db
from cinema_application.main import app

SQLALCHEMY_DATABASE_URL = "sqlite:///"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

SESSION_START_DATE = datetime.now() + timedelta(days=5)
SESSION_END_DATE = SESSION_START_DATE + timedelta(hours=3)


@pytest.fixture
def client():
    client = TestClient(app)
    yield client


@pytest.fixture
def override_get_db(monkeypatch):
    def mock_get_db():
        try:
            db = TestingSessionLocal()  # pylint: disable=invalid-name
            yield db
        finally:
            db.close()

    monkeypatch.setattr(app, "dependency_overrides", {get_db: mock_get_db})


@pytest.fixture
def authenticate_user(client, override_get_db):
    token = client.post(
        "/auth/token", data={"username": "string1", "password": "string"}
    ).json()["access_token"]
    yield token


def test_create_user(client, override_get_db):
    """
    Creating temporary user and using created user in all tests
    """
    response = client.post(
        "/auth",
        json={
            "email": "string1",
            "username": "string1",
            "first_name": "string",
            "last_name": "string",
            "password": "string",
            "role": "admin",
        },
    )
    assert response.status_code == 201


def test_create_movie(client, override_get_db, authenticate_user):
    todo_data = {"name": "Dune 2", "duration": 180}
    response = client.post(
        "/movies",
        headers={
            "accept": "application/json",
            "Authorization": f"Bearer {authenticate_user}",
        },
        json=todo_data,
    )
    assert response.status_code == 201


def test_create_room(client, override_get_db, authenticate_user):
    todo_data = {"name": "Red", "seats": 15}
    response = client.post(
        "/rooms",
        headers={
            "accept": "application/json",
            "Authorization": f"Bearer {authenticate_user}",
        },
        json=todo_data,
    )
    assert response.status_code == 201


def test_create_session(client, override_get_db, authenticate_user):
    todo_data = {
        "start_time": SESSION_START_DATE.strftime("%d-%m-%Y %H:%M"),
        "end_time": SESSION_END_DATE.strftime("%d-%m-%Y %H:%M"),
        "movie_id": 1,
        "room_id": 1,
    }
    response = client.post(
        "/sessions",
        headers={
            "accept": "application/json",
            "Authorization": f"Bearer {authenticate_user}",
        },
        json=todo_data,
    )
    assert response.status_code == 201


def test_sessions_filtered_by(client, override_get_db):
    response_by_movie_room = client.get(
        "/sessions/filtered/?movie_id=1&room_id=1",
        headers={
            "accept": "application/json",
        },
    )
    response_by_movie = client.get(
        "/sessions/filtered/?movie_id=1",
        headers={
            "accept": "application/json",
        },
    )
    response_by_room = client.get(
        "/sessions/filtered/?room_id=1",
        headers={
            "accept": "application/json",
        },
    )
    wrong_response = client.get(
        "/sessions/filtered/",
        headers={
            "accept": "application/json",
        },
    )

    sessions_data = [
        {
            "id": 1,
            "start_time": SESSION_START_DATE.strftime("%Y-%m-%dT%H:%M:00"),
            "end_time": SESSION_END_DATE.strftime("%Y-%m-%dT%H:%M:00"),
            "movie_id": 1,
            "room_id": 1,
        }
    ]
    assert response_by_movie.json() == sessions_data
    assert response_by_room.json() == sessions_data
    assert response_by_movie_room.json() == sessions_data
    assert wrong_response.status_code == 400


def test_session_by_id(client, override_get_db):
    session_data = {
        "session": {
            "start_time": SESSION_START_DATE.strftime("%Y-%m-%dT%H:%M:00"),
            "end_time": SESSION_END_DATE.strftime("%Y-%m-%dT%H:%M:00"),
            "room_id": 1,
            "id": 1,
            "movie_id": 1,
            "movie": {"duration": 180, "name": "Dune 2", "id": 1, "poster": None},
            "reservations": [],
            "room": {"seats": 15, "id": 1, "name": "Red"},
        },
        "reserved_seats": [],
        "available_seats": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
    }
    response = client.get(
        "/sessions/1/",
        headers={
            "accept": "application/json",
        },
    )
    wrong_response = client.get(
        "/sessions/5/",
        headers={
            "accept": "application/json",
        },
    )
    assert response.json() == session_data
    assert wrong_response.status_code == 404


def test_expired_sessions_filtered_by(client, override_get_db, authenticate_user):
    start_date = datetime.strptime("14-03-1990 12:05", "%d-%m-%Y %H:%M")
    end_date = start_date + timedelta(hours=3)
    todo_data = {
        "start_time": start_date.strftime("%d-%m-%Y %H:%M"),
        "end_time": end_date.strftime("%d-%m-%Y %H:%M"),
        "movie_id": 1,
        "room_id": 1,
    }
    response = client.post(
        "/sessions",
        headers={
            "accept": "application/json",
            "Authorization": f"Bearer {authenticate_user}",
        },
        json=todo_data,
    )

    assert response.status_code == 201

    response = client.get(
        "/sessions/filtered/?movie_id=1&room_id=1",
        headers={
            "accept": "application/json",
        },
    )
    assert len(response.json()) == 1
    assert response.json()[0]["start_time"] != start_date.strftime("%Y-%m-%dT%H:%M:00")

    response = client.get(
        "/sessions",
        headers={
            "accept": "application/json",
            "Authorization": f"Bearer {authenticate_user}",
        },
    )
    assert len(response.json()) == 2
    assert start_date.strftime("%Y-%m-%dT%H:%M:00") in [
        item["start_time"] for item in response.json()
    ]
