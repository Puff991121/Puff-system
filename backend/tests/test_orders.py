from collections.abc import Generator
from datetime import date, timedelta
from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from openpyxl import Workbook
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import create_access_token
from app.main import app
from app.models import User
from app.services.orders import now

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


def order_payload(**changes: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "order_date": "2026-07-02",
        "requirement": "市场营销课程论文",
        "template": "学术论文标准版",
        "format": "无",
        "school": "复旦大学",
        "price": "299.00",
        "payment_method": "微信",
    }
    payload.update(changes)
    return payload


def test_orders_require_login(client: TestClient) -> None:
    response = client.get("/api/orders")
    assert response.status_code == 401


def test_order_crud_and_filters(client: TestClient, headers: dict[str, str]) -> None:
    created = client.post("/api/orders", headers=headers, json=order_payload())
    assert created.status_code == 201
    order = created.json()["data"]
    assert order["order_no"].startswith("PF-20260702-")
    assert order["order_date"] == "2026-07-02"
    assert order["price"] == "299.00"

    second = client.post(
        "/api/orders",
        headers=headers,
        json=order_payload(
            requirement="网页设计作业",
            format="Html",
            price="199.50",
            payment_method="支付宝",
        ),
    )
    assert second.status_code == 201

    listed = client.get("/api/orders?keyword=论文&payment_method=微信", headers=headers)
    assert listed.status_code == 200
    assert listed.json()["data"]["total"] == 1
    assert listed.json()["data"]["items"][0]["id"] == order["id"]

    updated = client.patch(
        f"/api/orders/{order['id']}",
        headers=headers,
        json={"order_date": "2026-07-08", "price": "399.00", "format": "Figma"},
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["order_date"] == "2026-07-08"
    assert updated.json()["data"]["price"] == "399.00"

    detail = client.get(f"/api/orders/{order['id']}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["data"]["format"] == "Figma"

    deleted = client.delete(f"/api/orders/{order['id']}", headers=headers)
    assert deleted.status_code == 200
    assert deleted.json()["data"] == {"deleted_id": order["id"]}
    assert client.get(f"/api/orders/{order['id']}", headers=headers).status_code == 404


def test_orders_are_isolated_by_user(client: TestClient, headers: dict[str, str]) -> None:
    created = client.post("/api/orders", headers=headers, json=order_payload()).json()["data"]
    other_headers = {"Authorization": f"Bearer {create_access_token('other')}"}

    assert client.get("/api/orders", headers=other_headers).json()["data"]["total"] == 0
    assert client.get(f"/api/orders/{created['id']}", headers=other_headers).status_code == 404


def test_order_validation(client: TestClient, headers: dict[str, str]) -> None:
    invalid = client.post(
        "/api/orders",
        headers=headers,
        json=order_payload(format="Sketch", price="0.001"),
    )
    assert invalid.status_code == 422

    invalid_range = client.get(
        "/api/orders?start_date=2026-07-31&end_date=2026-07-01",
        headers=headers,
    )
    assert invalid_range.status_code == 400


def test_export_orders(client: TestClient, headers: dict[str, str]) -> None:
    client.post("/api/orders", headers=headers, json=order_payload())
    response = client.get("/api/orders/export", headers=headers)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert response.content.startswith(b"PK")


def test_order_summary_is_scoped_and_aggregated(
    client: TestClient, headers: dict[str, str]
) -> None:
    today = now().date()
    month_start = today.replace(day=1)
    previous_month = month_start - timedelta(days=1)

    client.post(
        "/api/orders",
        headers=headers,
        json=order_payload(order_date=today.isoformat(), price="100.10"),
    )
    client.post(
        "/api/orders",
        headers=headers,
        json=order_payload(order_date=month_start.isoformat(), price="200.20"),
    )
    client.post(
        "/api/orders",
        headers=headers,
        json=order_payload(order_date=previous_month.isoformat(), price="300.30"),
    )
    other_headers = {"Authorization": f"Bearer {create_access_token('other')}"}
    client.post(
        "/api/orders",
        headers=other_headers,
        json=order_payload(order_date=today.isoformat(), price="999.00"),
    )

    response = client.get("/api/orders/summary", headers=headers)
    assert response.status_code == 200
    data = response.json()["data"]
    expected_today_count = 2 if month_start == today else 1
    expected_today_amount = "300.30" if month_start == today else "100.10"
    assert data["today_count"] == expected_today_count
    assert data["today_amount"] == expected_today_amount
    assert data["month_count"] == 2
    assert data["month_amount"] == "300.30"
    expected_year_count = 2 + int(previous_month.year == today.year)
    expected_year_amount = "600.60" if previous_month.year == today.year else "300.30"
    assert data["year_count"] == expected_year_count
    assert data["year_amount"] == expected_year_amount
    assert data["total_count"] == 3
    assert data["total_amount"] == "600.60"


def test_order_summary_uses_reference_date_for_month_and_year(
    client: TestClient, headers: dict[str, str]
) -> None:
    for order_date, price in (
        (date(2024, 3, 5), "100.00"),
        (date(2024, 3, 28), "200.00"),
        (date(2024, 8, 1), "300.00"),
        (date(2023, 3, 1), "400.00"),
    ):
        client.post(
            "/api/orders",
            headers=headers,
            json=order_payload(order_date=order_date.isoformat(), price=price),
        )

    response = client.get(
        "/api/orders/summary?reference_date=2024-03-15", headers=headers
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["month_count"] == 2
    assert data["month_amount"] == "300.00"
    assert data["year_count"] == 3
    assert data["year_amount"] == "600.00"


def test_order_trend_returns_all_months_and_is_scoped(
    client: TestClient, headers: dict[str, str]
) -> None:
    client.post(
        "/api/orders",
        headers=headers,
        json=order_payload(order_date="2026-01-05", price="100.10"),
    )
    client.post(
        "/api/orders",
        headers=headers,
        json=order_payload(order_date="2026-01-20", price="200.20"),
    )
    client.post(
        "/api/orders",
        headers=headers,
        json=order_payload(order_date="2026-07-01", price="300.30"),
    )
    other_headers = {"Authorization": f"Bearer {create_access_token('other')}"}
    client.post(
        "/api/orders",
        headers=other_headers,
        json=order_payload(order_date="2026-01-01", price="999.00"),
    )

    response = client.get("/api/orders/trend?year=2026", headers=headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["year"] == 2026
    assert len(data["items"]) == 12
    assert data["items"][0] == {"month": 1, "amount": "300.30", "count": 2}
    assert data["items"][6] == {"month": 7, "amount": "300.30", "count": 1}
    assert data["items"][11] == {"month": 12, "amount": "0.00", "count": 0}


def test_import_orders_allows_partial_success(client: TestClient, headers: dict[str, str]) -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["日期", "作业要求", "模板", "格式", "学校", "价格", "支付方式"])
    sheet.append(["2026-07-02", "网页设计作业", "课程模板", "Html", "复旦大学", 199, "微信"])
    sheet.append(["2026-07-03", "无效格式作业", "课程模板", "Sketch", "浙江大学", 299, "支付宝"])
    content = BytesIO()
    workbook.save(content)

    response = client.post(
        "/api/orders/import",
        headers=headers,
        files={
            "file": (
                "orders.xlsx",
                content.getvalue(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert response.status_code == 200
    result = response.json()["data"]
    assert result["total_rows"] == 2
    assert result["success_count"] == 1
    assert result["failed_count"] == 1
    assert result["errors"][0]["row"] == 3
