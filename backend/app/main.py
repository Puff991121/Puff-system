from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.name,
        version="0.1.0",
        debug=settings.debug,
        docs_url="/docs" if settings.docs_enabled else None,
        redoc_url="/redoc" if settings.docs_enabled else None,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router, prefix="/api")

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
        message = exc.detail if isinstance(exc.detail, str) else "请求处理失败"
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": exc.status_code * 100, "message": message, "data": None},
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        first_error = exc.errors()[0] if exc.errors() else None
        message = first_error.get("msg", "请求参数校验失败") if first_error else "请求参数校验失败"
        return JSONResponse(
            status_code=422,
            content={"code": 42200, "message": message, "data": None},
        )

    @app.get("/", tags=["系统"], summary="服务入口")
    async def root() -> dict[str, str]:
        return {
            "name": settings.name,
            "status": "running",
            "docs": "/docs" if settings.docs_enabled else "disabled",
        }

    return app


app = create_app()
