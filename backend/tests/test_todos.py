from collections.abc import Generator
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import create_access_token
from app.main import app
from app.models import User

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSession = sessionmaker(bind=engine, expire_on_commit=False)


def override_get_db() -> Generator[Session, None, None]:
    with TestingSession() as db:
        yield db


@pytest.fixture(autouse=True)
def database() -> Generator[None, None, None]:
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(engine)
    with TestingSession() as db:
        db.add_all(
            [
                User(username="admin", password_hash="unused"),
                User(username="other", password_hash="unused"),
            ]
        )
        db.commit()
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token('admin')}"}


def payload(**changes):
    data = {
        "title": "完成日报",
        "description": "整理今日进展和明日计划",
        "period_type": "daily",
        "scheduled_date": date.today().isoformat(),
        "priority": "high",
    }
    data.update(changes)
    return data


def test_todo_crud_and_filters(client: TestClient, headers: dict[str, str]) -> None:
    created = client.post("/api/todos", headers=headers, json=payload())
    assert created.status_code == 201
    item = created.json()["data"]
    assert item["status"] == "pending"

    client.post(
        "/api/todos",
        headers=headers,
        json=payload(title="周度复盘", period_type="weekly", priority="medium"),
    )
    listed = client.get("/api/todos?period_type=daily&keyword=日报", headers=headers)
    assert listed.status_code == 200
    assert listed.json()["data"]["total"] == 1

    changed = client.patch(
        f"/api/todos/{item['id']}",
        headers=headers,
        json={"status": "completed", "title": "日报已提交"},
    )
    assert changed.status_code == 200
    assert changed.json()["data"]["completed_at"] is not None
    completed = client.get("/api/todos?status=completed", headers=headers)
    assert completed.json()["data"]["total"] == 1

    reopened = client.patch(f"/api/todos/{item['id']}", headers=headers, json={"status": "pending"})
    assert reopened.json()["data"]["completed_at"] is None
    assert client.delete(f"/api/todos/{item['id']}", headers=headers).status_code == 200
    assert client.get(f"/api/todos/{item['id']}", headers=headers).status_code == 404


def test_todo_summary_and_overdue(client: TestClient, headers: dict[str, str]) -> None:
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    client.post("/api/todos", headers=headers, json=payload(scheduled_date=yesterday))
    client.post(
        "/api/todos",
        headers=headers,
        json=payload(title="月度结算", period_type="monthly", status="completed"),
    )
    summary = client.get("/api/todos/summary", headers=headers).json()["data"]
    assert summary == {
        "total": 2,
        "pending": 1,
        "completed": 1,
        "overdue": 1,
        "daily": 1,
        "weekly": 0,
        "monthly": 1,
        "completion_rate": 50,
    }


def test_pending_todos_are_listed_before_completed(
    client: TestClient, headers: dict[str, str]
) -> None:
    client.post(
        "/api/todos",
        headers=headers,
        json=payload(title="已完成事项", status="completed"),
    )
    client.post(
        "/api/todos",
        headers=headers,
        json=payload(title="待完成事项", status="pending"),
    )

    items = client.get("/api/todos", headers=headers).json()["data"]["items"]

    assert [item["status"] for item in items] == ["pending", "completed"]


def test_todo_validation_auth_and_user_isolation(
    client: TestClient, headers: dict[str, str]
) -> None:
    assert client.get("/api/todos").status_code == 401
    assert client.post("/api/todos", headers=headers, json=payload(title="  ")).status_code == 422
    invalid_period = client.post("/api/todos", headers=headers, json=payload(period_type="yearly"))
    assert invalid_period.status_code == 422
    missing = client.patch("/api/todos/999", headers=headers, json={"status": "completed"})
    assert missing.status_code == 404
    assert client.patch("/api/todos/999", headers=headers, json={}).status_code == 422
    invalid_range = client.get(
        "/api/todos?start_date=2026-09-10&end_date=2026-09-01", headers=headers
    )
    assert invalid_range.status_code == 400

    item = client.post("/api/todos", headers=headers, json=payload()).json()["data"]
    other_headers = {"Authorization": f"Bearer {create_access_token('other')}"}
    assert client.get(f"/api/todos/{item['id']}", headers=other_headers).status_code == 404
    assert client.delete(f"/api/todos/{item['id']}", headers=other_headers).status_code == 404
