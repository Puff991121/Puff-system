from __future__ import annotations

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
from app.schemas.template import extract_share_url

SHARE = (
    "通过网盘分享的文件：云肩-源代码\n"
    "链接: https://pan.baidu.com/s/1y370s39wOHx4sxifc1KNtw?pwd=rsik 提取码: rsik"
)
SHARE_WITHOUT_PWD = "链接：https://pan.baidu.com/s/example 提取码：a1b2"
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
    return {"name": "云肩", "notes": "传统文化主题", "html_share": SHARE, **changes}


def test_template_crud_keeps_full_share_text(client: TestClient, headers: dict[str, str]) -> None:
    shares = {
        f"{format_name}_share": SHARE for format_name in ("figma", "psd", "xd", "jsd", "material")
    }
    created = client.post("/api/templates", headers=headers, json=payload(**shares))
    assert created.status_code == 201
    item = created.json()["data"]
    for field in (*shares, "html_share"):
        assert item[field] == SHARE
    assert item["share_urls"] == {
        format_name: "https://pan.baidu.com/s/1y370s39wOHx4sxifc1KNtw?pwd=rsik"
        for format_name in ("Figma", "Psd", "Xd", "Jsd", "Html", "素材")
    }
    assert "user_id" not in item
    assert item["created_at"].endswith("+08:00")
    item_url = f"/api/templates/{item['id']}"
    assert client.get(item_url, headers=headers).json()["data"]["name"] == "云肩"

    changed = client.patch(
        item_url,
        headers=headers,
        json={
            "name": " 云肩新版 ",
            "notes": "  ",
            "figma_share": None,
            "html_share": SHARE_WITHOUT_PWD,
        },
    )
    assert changed.status_code == 200
    updated = changed.json()["data"]
    assert updated["name"] == "云肩新版"
    assert updated["notes"] is None
    assert updated["figma_share"] is None
    assert updated["psd_share"] == SHARE
    assert updated["html_share"] == SHARE_WITHOUT_PWD
    assert updated["share_urls"]["Html"] == "https://pan.baidu.com/s/example?pwd=a1b2"
    assert client.delete(item_url, headers=headers).json()["data"]["deleted_id"] == item["id"]
    assert client.get(item_url, headers=headers).status_code == 404
    assert client.get("/api/templates", headers=headers).json()["data"]["total"] == 0


def test_template_material_create_read_update_and_clear(
    client: TestClient, headers: dict[str, str]
) -> None:
    existing = client.post("/api/templates", headers=headers, json=payload()).json()["data"]
    assert existing["material_share"] is None
    assert existing["share_urls"]["素材"] is None

    created = client.post(
        "/api/templates",
        headers=headers,
        json=payload(name="云肩素材", html_share=None, material_share=SHARE_WITHOUT_PWD),
    )
    assert created.status_code == 201
    item = created.json()["data"]
    item_url = f"/api/templates/{item['id']}"
    assert item["material_share"] == SHARE_WITHOUT_PWD
    assert item["share_urls"]["素材"] == "https://pan.baidu.com/s/example?pwd=a1b2"
    listed = client.get("/api/templates?keyword=云肩素材", headers=headers).json()["data"]
    assert listed["items"][0]["material_share"] == SHARE_WITHOUT_PWD
    assert (
        client.get(item_url, headers=headers).json()["data"]["material_share"] == SHARE_WITHOUT_PWD
    )

    updated = client.patch(item_url, headers=headers, json={"material_share": SHARE})
    assert updated.status_code == 200
    assert updated.json()["data"]["material_share"] == SHARE
    assert client.patch(item_url, headers=headers, json={"material_share": None}).status_code == 422
    assert client.get(item_url, headers=headers).json()["data"]["material_share"] == SHARE

    cleared = client.patch(
        item_url, headers=headers, json={"material_share": "  ", "html_share": SHARE_WITHOUT_PWD}
    )
    assert cleared.status_code == 200
    assert cleared.json()["data"]["material_share"] is None
    assert cleared.json()["data"]["share_urls"]["素材"] is None
    assert cleared.json()["data"]["html_share"] == SHARE_WITHOUT_PWD


def test_template_search_pagination_and_oldest_updated_order(
    client: TestClient, headers: dict[str, str]
) -> None:
    first = client.post("/api/templates", headers=headers, json=payload()).json()["data"]
    second = client.post(
        "/api/templates", headers=headers, json=payload(name="刺绣", notes="包含 100%_design 文件")
    ).json()["data"]
    page = client.get("/api/templates?page_size=1", headers=headers).json()["data"]
    assert page["total"] == 2
    assert page["total_pages"] == 2
    assert page["items"][0]["id"] == first["id"]
    next_page = client.get("/api/templates?page_size=1&page=2", headers=headers).json()["data"]
    assert next_page["items"][0]["id"] == second["id"]
    for keyword in ("云肩", "传统文化", " 云肩 "):
        found = client.get("/api/templates", headers=headers, params={"keyword": keyword})
        assert found.json()["data"]["items"][0]["id"] == first["id"]
    literal = client.get("/api/templates", headers=headers, params={"keyword": "%_"})
    assert literal.json()["data"]["total"] == 1
    assert literal.json()["data"]["items"][0]["id"] == second["id"]
    assert client.get("/api/templates?keyword=不存在", headers=headers).json()["data"]["total"] == 0
    client.patch(f"/api/templates/{first['id']}", headers=headers, json={"notes": "最新修改"})
    items = client.get("/api/templates", headers=headers).json()["data"]["items"]
    assert [item["id"] for item in items] == [second["id"], first["id"]]


def test_template_name_uniqueness_on_create_and_update(
    client: TestClient, headers: dict[str, str]
) -> None:
    first = client.post("/api/templates", headers=headers, json=payload()).json()["data"]
    assert (
        client.post("/api/templates", headers=headers, json=payload(name=" 云肩 ")).status_code
        == 409
    )
    second = client.post("/api/templates", headers=headers, json=payload(name="刺绣")).json()[
        "data"
    ]
    duplicate = client.patch(
        f"/api/templates/{second['id']}", headers=headers, json={"name": "云肩"}
    )
    assert duplicate.status_code == 409
    unchanged = client.get(f"/api/templates/{second['id']}", headers=headers).json()["data"]
    assert unchanged["name"] == "刺绣"
    assert client.delete(f"/api/templates/{first['id']}", headers=headers).status_code == 200
    assert client.post("/api/templates", headers=headers, json=payload()).status_code == 201


def test_templates_require_login_and_isolate_all_operations(
    client: TestClient, headers: dict[str, str]
) -> None:
    assert client.get("/api/templates").status_code == 401
    assert client.post("/api/templates", json=payload()).status_code == 401
    item = client.post("/api/templates", headers=headers, json=payload()).json()["data"]
    item_url = f"/api/templates/{item['id']}"
    other = {"Authorization": f"Bearer {create_access_token('other')}"}
    assert client.get("/api/templates", headers=other).json()["data"]["total"] == 0
    assert client.get(item_url, headers=other).status_code == 404
    assert client.patch(item_url, headers=other, json={"name": "篡改"}).status_code == 404
    assert client.delete(item_url, headers=other).status_code == 404
    assert client.get(item_url).status_code == 401
    assert client.patch(item_url, json={"name": "篡改"}).status_code == 401
    assert client.delete(item_url).status_code == 401
    assert client.post("/api/templates", headers=other, json=payload()).status_code == 201


@pytest.mark.parametrize(
    "changes",
    [
        {"name": "  "},
        {"name": None},
        {"name": "长" * 101},
        {"html_share": None},
        {"html_share": "  "},
        {"html_share": "没有链接"},
        {"html_share": "https://pan.baidu.com.evil.test/s/file"},
        {"html_share": "https://pan.baidu.com@evil.test/s/file"},
        {"html_share": "javascript:alert(1)"},
        {"html_share": "https://pan.baidu.com/"},
        {"html_share": "https://pan.baidu.com/s/file", "figma_share": "错误的链接"},
        {"html_share": "长" * 2001},
        {"material_share": "没有链接"},
        {"material_share": "https://pan.baidu.com.evil.test/s/material"},
        {"material_share": "长" * 2001},
        {"notes": "长" * 1001},
        {"unknown_format": SHARE},
    ],
)
def test_template_rejects_invalid_create(
    client: TestClient, headers: dict[str, str], changes: dict
) -> None:
    assert (
        client.post("/api/templates", headers=headers, json=payload(**changes)).status_code == 422
    )
    assert client.get("/api/templates", headers=headers).json()["data"]["total"] == 0


def test_template_partial_update_cannot_remove_last_share(
    client: TestClient, headers: dict[str, str]
) -> None:
    item = client.post("/api/templates", headers=headers, json=payload()).json()["data"]
    item_url = f"/api/templates/{item['id']}"
    for changes in ({}, {"name": None}, {"name": "  "}, {"html_share": ""}, {"html_share": None}):
        assert client.patch(item_url, headers=headers, json=changes).status_code == 422
    assert client.get(item_url, headers=headers).json()["data"]["html_share"] == SHARE
    replaced = client.patch(
        item_url, headers=headers, json={"html_share": None, "jsd_share": SHARE_WITHOUT_PWD}
    )
    assert replaced.status_code == 200
    assert replaced.json()["data"]["html_share"] is None
    assert replaced.json()["data"]["jsd_share"] == SHARE_WITHOUT_PWD


def test_template_missing_and_query_validation(client: TestClient, headers: dict[str, str]) -> None:
    for query in ("page=0", "page_size=0", "page_size=101", "keyword=" + "长" * 101):
        assert client.get(f"/api/templates?{query}", headers=headers).status_code == 422
    assert client.get("/api/templates/999", headers=headers).status_code == 404
    assert (
        client.patch("/api/templates/999", headers=headers, json={"name": "新名称"}).status_code
        == 404
    )
    assert client.delete("/api/templates/999", headers=headers).status_code == 404


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        (f"（{SHARE}）", "https://pan.baidu.com/s/1y370s39wOHx4sxifc1KNtw?pwd=rsik"),
        (SHARE_WITHOUT_PWD, "https://pan.baidu.com/s/example?pwd=a1b2"),
        ("https://pan.baidu.com/s/file", "https://pan.baidu.com/s/file"),
        ("(https://pan.baidu.com/s/file)", "https://pan.baidu.com/s/file"),
        (
            "https://pan.baidu.com/s/file?pwd=abcd 提取码：efgh",
            "https://pan.baidu.com/s/file?pwd=abcd",
        ),
        ("https://pan.baidu.com/s/file?pwd= 提取码：a1b2", "https://pan.baidu.com/s/file?pwd=a1b2"),
        (
            "https://pan.baidu.com/s/file?from=share#list 提取码：a1b2",
            "https://pan.baidu.com/s/file?from=share&pwd=a1b2#list",
        ),
        (
            "https://pan.baidu.com/share/init?surl=file 提取码：a1b2",
            "https://pan.baidu.com/share/init?surl=file&pwd=a1b2",
        ),
        (
            "https://pan.baidu.com/share/link?shareid=1&uk=2",
            "https://pan.baidu.com/share/link?shareid=1&uk=2",
        ),
        ("https://pan.baidu.com:bad/s/file", None),
        ("https://user:password@pan.baidu.com/s/file", None),
        ("https://pan.baidu.com:9999/s/file", None),
        ("https://evil.test/s/file", None),
        (None, None),
    ],
)
def test_extract_baidu_share_url(content: str | None, expected: str | None) -> None:
    assert extract_share_url(content) == expected
