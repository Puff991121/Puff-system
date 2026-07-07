from collections.abc import Generator

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


def test_account_data_crud_fields_and_summary() -> None:
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {create_access_token('admin')}"}
    page = client.get("/api/account-data", headers=headers)
    assert [x["key"] for x in page.json()["data"]["fields"]] == ["account", "followers", "notes"]

    created = client.post(
        "/api/account-data/records",
        headers=headers,
        json={"values": {"account": " 测试账号 ", "followers": 12}},
    )
    assert created.status_code == 201
    record = created.json()["data"]["record"]
    assert record["values"] == {"account": "测试账号", "followers": 12, "notes": 0}

    field = client.post(
        "/api/account-data/fields", headers=headers, json={"label": "获赞数", "type": "number"}
    )
    assert field.status_code == 201
    field_id = field.json()["data"]["field"]["id"]
    page = client.get("/api/account-data", headers=headers).json()["data"]
    key = page["fields"][-1]["key"]
    assert page["records"][0]["values"][key] == 0

    updated = client.patch(
        f"/api/account-data/records/{record['id']}",
        headers=headers,
        json={"values": {"followers": 20, key: 5}},
    )
    assert updated.json()["data"]["summary"]["total_followers"] == 20
    assert (
        client.patch(
            f"/api/account-data/records/{record['id']}",
            headers=headers,
            json={"values": {"followers": -1}},
        ).status_code
        == 400
    )
    assert client.delete(f"/api/account-data/fields/{field_id}", headers=headers).status_code == 200
    assert (
        client.delete(
            f"/api/account-data/fields/{page['fields'][0]['id']}", headers=headers
        ).status_code
        == 403
    )
    assert (
        client.delete(f"/api/account-data/records/{record['id']}", headers=headers).json()["data"][
            "summary"
        ]["account_count"]
        == 0
    )


def test_account_data_auth_duplicate_and_isolation() -> None:
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {create_access_token('admin')}"}
    assert client.get("/api/account-data").status_code == 401
    assert (
        client.post(
            "/api/account-data/fields", headers=headers, json={"label": "分类", "type": "text"}
        ).status_code
        == 201
    )
    assert (
        client.post(
            "/api/account-data/fields", headers=headers, json={"label": "分类", "type": "text"}
        ).status_code
        == 409
    )
    client.post(
        "/api/account-data/records", headers=headers, json={"values": {"account": "仅自己可见"}}
    )
    other = {"Authorization": f"Bearer {create_access_token('other')}"}
    assert client.get("/api/account-data", headers=other).json()["data"]["records"] == []
