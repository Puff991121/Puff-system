from fastapi import APIRouter

from app.api.routes import (
    account_data,
    assets,
    auth,
    expenses,
    health,
    orders,
    templates,
    todos,
    xianyu_links,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["系统"])
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(orders.router, prefix="/orders", tags=["订单"])
api_router.include_router(templates.router, prefix="/templates", tags=["模板"])
api_router.include_router(xianyu_links.router, prefix="/xianyu-links", tags=["闲鱼链接"])
api_router.include_router(assets.router, prefix="/assets", tags=["资产"])
api_router.include_router(account_data.router, prefix="/account-data", tags=["账号数据"])
api_router.include_router(expenses.router, prefix="/expenses", tags=["消费记录"])
api_router.include_router(todos.router, prefix="/todos", tags=["待办事项"])
