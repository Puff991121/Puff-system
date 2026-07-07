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

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
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


def test_assets_require_login(client: TestClient) -> None:
    assert client.get("/api/assets").status_code == 401


def test_asset_account_crud_and_summary(client: TestClient, headers: dict[str, str]) -> None:
    asset = client.post(
        "/api/assets/accounts",
        headers=headers,
        json={"type": "asset", "account": "微信", "amount": "1000.10"},
    )
    assert asset.status_code == 201
    asset_data = asset.json()["data"]
    assert asset_data["account"]["sort_order"] == 1
    assert asset_data["summary"]["total_assets"] == "1000.10"

    liability = client.post(
        "/api/assets/accounts",
        headers=headers,
        json={"type": "liability", "account": "花呗", "amount": "-100.10"},
    )
    assert liability.status_code == 201
    summary = liability.json()["data"]["summary"]
    assert summary["total_liabilities"] == "-100.10"
    assert summary["net_assets"] == "900.00"
    assert summary["liability_ratio"] == "10.01"

    account_id = asset_data["account"]["id"]
    updated = client.patch(
        f"/api/assets/accounts/{account_id}",
        headers=headers,
        json={"account": "微信零钱", "amount": "1200.00", "sort_order": 2},
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["account"]["account"] == "微信零钱"
    assert updated.json()["data"]["summary"]["net_assets"] == "1099.90"

    page = client.get("/api/assets", headers=headers)
    assert page.status_code == 200
    assert len(page.json()["data"]["assets"]) == 1
    assert len(page.json()["data"]["liabilities"]) == 1

    deleted = client.delete(f"/api/assets/accounts/{account_id}", headers=headers)
    assert deleted.status_code == 200
    assert deleted.json()["data"]["deleted_id"] == account_id
    assert deleted.json()["data"]["summary"]["total_assets"] == "0.00"


def test_asset_validation_duplicate_and_isolation(
    client: TestClient, headers: dict[str, str]
) -> None:
    invalid_asset = client.post(
        "/api/assets/accounts",
        headers=headers,
        json={"type": "asset", "account": "错误资产", "amount": "-1.00"},
    )
    assert invalid_asset.status_code == 422

    invalid_liability = client.post(
        "/api/assets/accounts",
        headers=headers,
        json={"type": "liability", "account": "错误负债", "amount": "1.00"},
    )
    assert invalid_liability.status_code == 422

    first = client.post(
        "/api/assets/accounts",
        headers=headers,
        json={"type": "asset", "account": "银行卡", "amount": "10.00"},
    )
    assert first.status_code == 201
    duplicate = client.post(
        "/api/assets/accounts",
        headers=headers,
        json={"type": "asset", "account": "银行卡", "amount": "20.00"},
    )
    assert duplicate.status_code == 409

    account_id = first.json()["data"]["account"]["id"]
    other_headers = {"Authorization": f"Bearer {create_access_token('other')}"}
    assert client.get("/api/assets", headers=other_headers).json()["data"]["assets"] == []
    assert (
        client.patch(
            f"/api/assets/accounts/{account_id}",
            headers=other_headers,
            json={"amount": "99.00"},
        ).status_code
        == 404
    )
