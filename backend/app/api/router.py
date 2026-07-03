from fastapi import APIRouter

from app.api.routes import auth, health, orders

api_router = APIRouter()
api_router.include_router(health.router, tags=["系统"])
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(orders.router, prefix="/orders", tags=["订单"])
