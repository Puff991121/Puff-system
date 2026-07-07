from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.asset import (
    AssetAccountCreate,
    AssetAccountRead,
    AssetAccountUpdate,
    AssetDeleteResult,
    AssetMutationResult,
    AssetPageData,
    AssetResponse,
)
from app.services.assets import (
    create_account,
    delete_account,
    get_account,
    get_accounts,
    get_summary,
    update_account,
)

router = APIRouter()
Db = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


def response(data, message: str = "success") -> dict:  # type: ignore[no-untyped-def]
    return {"code": 0, "message": message, "data": data}


def not_found() -> HTTPException:
    return HTTPException(status_code=404, detail="资产账户不存在")


def conflict() -> HTTPException:
    return HTTPException(status_code=409, detail="同类型账户名称已存在")


@router.get("", response_model=AssetResponse[AssetPageData], summary="获取资产页面数据")
def asset_page(db: Db, current_user: CurrentUser) -> dict:
    return response(
        AssetPageData(
            summary=get_summary(db, current_user.id),
            assets=[
                AssetAccountRead.model_validate(item)
                for item in get_accounts(db, current_user.id, "asset")
            ],
            liabilities=[
                AssetAccountRead.model_validate(item)
                for item in get_accounts(db, current_user.id, "liability")
            ],
        )
    )


@router.post(
    "/accounts",
    status_code=201,
    response_model=AssetResponse[AssetMutationResult],
    summary="新增资产账户",
)
def add_account(payload: AssetAccountCreate, db: Db, current_user: CurrentUser) -> dict:
    try:
        account = create_account(db, current_user.id, payload)
    except IntegrityError as exc:
        raise conflict() from exc
    return response(
        AssetMutationResult(
            account=AssetAccountRead.model_validate(account),
            summary=get_summary(db, current_user.id),
        ),
        "账户新增成功",
    )


@router.patch(
    "/accounts/{account_id}",
    response_model=AssetResponse[AssetMutationResult],
    summary="修改资产账户",
)
def edit_account(
    account_id: int,
    payload: AssetAccountUpdate,
    db: Db,
    current_user: CurrentUser,
) -> dict:
    account = get_account(db, current_user.id, account_id)
    if account is None:
        raise not_found()
    try:
        account = update_account(db, account, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except IntegrityError as exc:
        raise conflict() from exc
    return response(
        AssetMutationResult(
            account=AssetAccountRead.model_validate(account),
            summary=get_summary(db, current_user.id),
        ),
        "账户更新成功",
    )


@router.delete(
    "/accounts/{account_id}",
    response_model=AssetResponse[AssetDeleteResult],
    summary="删除资产账户",
)
def remove_account(account_id: int, db: Db, current_user: CurrentUser) -> dict:
    account = get_account(db, current_user.id, account_id)
    if account is None:
        raise not_found()
    delete_account(db, account)
    return response(
        AssetDeleteResult(deleted_id=account_id, summary=get_summary(db, current_user.id)),
        "账户删除成功",
    )
