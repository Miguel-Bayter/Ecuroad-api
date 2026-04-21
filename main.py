import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.admin.router import router as admin_router
from app.api.carreras.router import router as carreras_router
from app.api.perfiles.router import router as perfiles_router
from app.core.exceptions import (
    CarreraNotFound,
    IntegrityCheckError,
    PerfilNotFound,
    SSRFBlockedError,
)
from app.db.mongodb import close_db, connect_db, ensure_initialized
from app.middleware.auth import SessionTokenMiddleware
from app.middleware.logging_mw import RequestLoggingMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.utils.logger import get_logger
from config import get_settings

logger = get_logger()
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    logger.info("database_connected")
    yield
    await close_db()
    logger.info("database_disconnected")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="EduRoad API",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url=None,
    )
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Middleware registration order: last added = outermost layer.
    # Desired outermost-first: Security → Logging → force_https → CORS → Session
    # add_middleware calls must therefore be in reverse: Session, CORS, Logging, Security.
    app.add_middleware(SessionTokenMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.CLIENT_ORIGIN],
        allow_methods=["GET", "POST", "PATCH"],
        allow_headers=["Content-Type", "X-Session-Token"],
        max_age=600,
    )
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)

    @app.middleware("http")
    async def ensure_db(request: Request, call_next):
        await ensure_initialized()
        return await call_next(request)

    @app.middleware("http")
    async def force_https(request: Request, call_next):
        if settings.FORCE_HTTPS and request.headers.get("x-forwarded-proto") == "http":
            return RedirectResponse(
                url=str(request.url).replace("http://", "https://", 1),
                status_code=301,
            )
        return await call_next(request)

    @app.exception_handler(CarreraNotFound)
    async def carrera_not_found_handler(request, exc):
        return JSONResponse(status_code=404, content={"error": str(exc) or "Career not found"})

    @app.exception_handler(PerfilNotFound)
    async def perfil_not_found_handler(request, exc):
        return JSONResponse(status_code=404, content={"error": str(exc) or "Profile not found"})

    @app.exception_handler(SSRFBlockedError)
    async def ssrf_blocked_handler(request, exc):
        return JSONResponse(status_code=400, content={"error": str(exc)})

    @app.exception_handler(IntegrityCheckError)
    async def integrity_error_handler(request, exc):
        return JSONResponse(status_code=422, content={"error": str(exc)})

    @app.exception_handler(Exception)
    async def global_error_handler(request, exc):
        logger.error("unhandled_exception", error=str(exc), path=request.url.path)
        return JSONResponse(status_code=500, content={"error": "Internal server error"})

    app.include_router(carreras_router, prefix="/api/carreras", tags=["carreras"])
    app.include_router(perfiles_router, prefix="/api/perfiles", tags=["perfiles"])
    app.include_router(admin_router, prefix="/api/admin", tags=["admin"])

    @app.get("/", include_in_schema=False)
    async def root():
        return RedirectResponse(url="/api/docs")

    @app.get("/api/health")
    async def health():
        from app.models.carrera import Carrera

        db_status = "disconnected"
        try:
            await Carrera.find_one()
            db_status = "connected"
        except Exception:
            db_status = "error"
        return {
            "status": "ok" if db_status == "connected" else "degraded",
            "uptime": time.time(),
            "db": db_status,
            "version": "0.1.0",
        }

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run("main:app", host="0.0.0.0", port=settings.PORT, reload=True)
