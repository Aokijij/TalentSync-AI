from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.v1.router import api_router
from app.application.errors import UseCaseError
from app.core.config import settings
from app.core.limiter import limiter


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        description="API REST para TalentSync AI, plataforma de matching laboral con NLP.",
        version="0.1.0",
    )

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]
        if settings.environment == "development"
        else ["talentsync.ai", "*.talentsync.ai"],
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

    @app.exception_handler(UseCaseError)
    async def use_case_error_handler(request: Request, exc: UseCaseError):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    app.include_router(api_router, prefix="/api/v1")

    @app.get("/health", tags=["health"])
    def health_check() -> dict[str, str]:
        return {"status": "ok", "service": settings.app_name}

    return app


app = create_app()
