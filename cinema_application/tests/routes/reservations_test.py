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
    todo_data = {"name": "Red", "seats": 5}
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


def test_create_reservation(client, override_get_db, authenticate_user):
    todo_data = {"seat": 3, "session_id": 1, "contact": "example@gmail.com"}
    response = client.post(
        "/reservations",
        headers={
            "accept": "application/json",
            "Authorization": f"Bearer {authenticate_user}",
        },
        json=todo_data,
    )
    assert response.status_code == 201


def test_session_reservations(client, override_get_db):
    response = client.get(
        "/reservations/by_sessions/1",
        headers={
            "accept": "application/json",
        },
    )
    assert response.json() == [
        {"id": 1, "seat": 3, "session_id": 1, "contact": "example@gmail.com"}
    ]
