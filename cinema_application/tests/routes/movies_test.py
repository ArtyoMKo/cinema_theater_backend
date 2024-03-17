import pytest
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


@pytest.fixture
def client():
    client = TestClient(app)
    yield client


@pytest.fixture
def override_get_db(monkeypatch):
    def mock_get_db():
        try:
            db = TestingSessionLocal()
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
    todo_data = {"name": "Dune 2", "duration": 180, "poster": "bytes"}
    response = client.post(
        "/movies",
        headers={
            "accept": "application/json",
            "Authorization": f"Bearer {authenticate_user}",
        },
        json=todo_data,
    )
    assert response.status_code == 201


def test_read_all(client, override_get_db, authenticate_user):
    response = client.get(
        "/movies",
        headers={
            "accept": "application/json",
            "Authorization": f"Bearer {authenticate_user}",
        },
    )
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json() == [{"id": 1, "name": "Dune 2", "duration": 180, "poster": "bytes"}]


def test_get_movie_by_id(client, override_get_db):
    response = client.get(
        "/movies/1",
        headers={"accept": "application/json"},
    )
    assert response.status_code == 200
    assert response.json() == {"id": 1, "name": "Dune 2", "duration": 180, "poster": "bytes"}


def test_delete_movie(client, override_get_db, authenticate_user):
    response = client.delete(
        "/movies/1",
        headers={
            "accept": "application/json",
            "Authorization": f"Bearer {authenticate_user}",
        },
    )
    assert response.status_code == 204
    # --- Negative
    response = client.delete(
        "/rooms/1",
        headers={"accept": "application/json", "Authorization": f"Bearer wrong token"},
    )
    assert response.status_code == 401
