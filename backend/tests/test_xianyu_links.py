from __future__ import annotations

from collections.abc import Generator
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import create_access_token
from app.main import app
from app.models import User, XianyuLink

LINK = "https://www.goofish.com/item?id=123456789&spm=a%2Fb#detail"
SHORT_LINK = "https://m.tb.cn/h.example?tk=aBc123"
SHARE_LINK = (
    "【闲鱼】https://m.tb.cn/h.j4M3WAA?tk=rlj8TC9Tio5 CZ001 「我在闲鱼发【网页设计】」\n"
    "点击链接直接打开"
)
MARKDOWN_SHARE_LINK = (
    "【闲鱼】[https://m.tb.cn/h.j4M3WAA?tk=rlj8TC9Tio5]"
    "(https://m.tb.cn/h.j4M3WAA?tk=rlj8TC9Tio5) CZ001 「我在闲鱼发【网页设计】」\n"
    "点击链接直接打开"
)
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
    return {"title": "云肩网页设计模板", "link": LINK, **changes}


def test_xianyu_link_crud_preserves_url(client: TestClient, headers: dict[str, str]) -> None:
    created = client.post(
        "/api/xianyu-links",
        headers=headers,
        json=payload(title=" 云肩网页设计模板 ", link=f" {LINK} "),
    )
    assert created.status_code == 201
    item = created.json()["data"]
    assert item["title"] == "云肩网页设计模板"
    assert item["link"] == LINK
    assert "user_id" not in item
    assert item["created_at"].endswith("+08:00")
    item_url = f"/api/xianyu-links/{item['id']}"
    assert client.get(item_url, headers=headers).json()["data"]["link"] == LINK

    renamed = client.patch(item_url, headers=headers, json={"title": "新版云肩"})
    assert renamed.status_code == 200
    assert renamed.json()["data"]["link"] == LINK
    updated = client.patch(item_url, headers=headers, json={"link": SHARE_LINK})
    assert updated.status_code == 200
    assert updated.json()["data"]["title"] == "新版云肩"
    assert updated.json()["data"]["link"] == SHARE_LINK
    assert client.get(item_url, headers=headers).json()["data"]["link"] == SHARE_LINK
    assert (
        client.get("/api/xianyu-links", headers=headers).json()["data"]["items"][0]["link"]
        == SHARE_LINK
    )
    assert updated.json()["data"]["updated_at"] >= item["updated_at"]
    assert client.delete(item_url, headers=headers).json()["data"]["deleted_id"] == item["id"]
    assert client.get(item_url, headers=headers).status_code == 404
    assert client.get("/api/xianyu-links", headers=headers).json()["data"]["total"] == 0


def test_xianyu_search_pagination_and_oldest_updated_order(
    client: TestClient, headers: dict[str, str]
) -> None:
    first = client.post("/api/xianyu-links", headers=headers, json=payload()).json()["data"]
    second = client.post(
        "/api/xianyu-links", headers=headers, json=payload(title="100%_设计", link=SHORT_LINK)
    ).json()["data"]
    # Equal timestamps must still produce stable pagination.
    with TestingSession() as db:
        for item_id in (first["id"], second["id"]):
            db.get(XianyuLink, item_id).updated_at = datetime(2026, 1, 1)
        db.commit()
    first_page = client.get("/api/xianyu-links?page_size=1", headers=headers).json()["data"]
    assert first_page["total"] == 2
    assert first_page["total_pages"] == 2
    assert first_page["items"][0]["id"] == first["id"]
    second_page = client.get("/api/xianyu-links?page_size=1&page=2", headers=headers).json()["data"]
    assert second_page["items"][0]["id"] == second["id"]
    for keyword in ("云肩", "123456789", " 云肩 "):
        found = client.get("/api/xianyu-links", headers=headers, params={"keyword": keyword})
        assert found.json()["data"]["total"] == 1
        assert found.json()["data"]["items"][0]["id"] == first["id"]
    for keyword in ("%_", "aBc123"):
        found = client.get("/api/xianyu-links", headers=headers, params={"keyword": keyword})
        assert found.json()["data"]["total"] == 1
        assert found.json()["data"]["items"][0]["id"] == second["id"]
    assert (
        client.get("/api/xianyu-links?keyword=不存在", headers=headers).json()["data"]["total"] == 0
    )
    client.patch(f"/api/xianyu-links/{first['id']}", headers=headers, json={"title": "最新修改"})
    items = client.get("/api/xianyu-links", headers=headers).json()["data"]["items"]
    assert [item["id"] for item in items] == [second["id"], first["id"]]


def test_xianyu_auth_and_user_isolation(client: TestClient, headers: dict[str, str]) -> None:
    assert client.get("/api/xianyu-links").status_code == 401
    assert client.post("/api/xianyu-links", json=payload()).status_code == 401
    item = client.post("/api/xianyu-links", headers=headers, json=payload()).json()["data"]
    item_url = f"/api/xianyu-links/{item['id']}"
    other = {"Authorization": f"Bearer {create_access_token('other')}"}
    assert client.get("/api/xianyu-links", headers=other).json()["data"]["items"] == []
    assert client.get(item_url, headers=other).status_code == 404
    assert client.patch(item_url, headers=other, json={"title": "篡改"}).status_code == 404
    assert client.delete(item_url, headers=other).status_code == 404
    assert client.get(item_url).status_code == 401
    assert client.patch(item_url, json={"title": "篡改"}).status_code == 401
    assert client.delete(item_url).status_code == 401
    assert client.post("/api/xianyu-links", headers=other, json=payload()).status_code == 201


@pytest.mark.parametrize(
    "changes",
    [
        {"title": "  "},
        {"title": None},
        {"title": "长" * 201},
        {"link": ""},
        {"link": " \n\t "},
        {"link": None},
        {"link": 123},
        {"link": "https://example.com/" + "a" * 2000},
        {"notes": "不支持的字段"},
    ],
)
def test_xianyu_rejects_invalid_create(
    client: TestClient, headers: dict[str, str], changes: dict
) -> None:
    assert (
        client.post("/api/xianyu-links", headers=headers, json=payload(**changes)).status_code
        == 422
    )
    assert client.get("/api/xianyu-links", headers=headers).json()["data"]["total"] == 0


def test_xianyu_invalid_updates_and_missing_records(
    client: TestClient, headers: dict[str, str]
) -> None:
    item = client.post("/api/xianyu-links", headers=headers, json=payload()).json()["data"]
    item_url = f"/api/xianyu-links/{item['id']}"
    for changes in (
        {},
        {"title": None},
        {"title": "  "},
        {"link": None},
        {"link": " \n\t "},
        {"link": "长" * 2001},
    ):
        assert client.patch(item_url, headers=headers, json=changes).status_code == 422
    assert client.get(item_url, headers=headers).json()["data"]["link"] == LINK
    assert client.get("/api/xianyu-links/999", headers=headers).status_code == 404
    assert (
        client.patch("/api/xianyu-links/999", headers=headers, json={"title": "新标题"}).status_code
        == 404
    )
    assert client.delete("/api/xianyu-links/999", headers=headers).status_code == 404
    for query in ("page=0", "page_size=0", "page_size=101", "keyword=" + "长" * 201):
        assert client.get(f"/api/xianyu-links?{query}", headers=headers).status_code == 422


@pytest.mark.parametrize(
    "link",
    [
        LINK,
        SHORT_LINK,
        "http://example.com/item?id=1",
        "https://example.com/中文?x=1%2F2",
        SHARE_LINK,
        MARKDOWN_SHARE_LINK,
        "闲鱼分享文案",
    ],
)
def test_xianyu_keeps_original_links_and_share_text(
    client: TestClient, headers: dict[str, str], link: str
) -> None:
    created = client.post("/api/xianyu-links", headers=headers, json=payload(link=f" {link} "))
    assert created.status_code == 201
    assert created.json()["data"]["link"] == link
