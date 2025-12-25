from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes.itineraries import router as itineraries_router
from app.api.routes.trips import router as trips_router
from app.core.logging import configure_logging, get_logger, log_event
from app.dependencies import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(
        log_level=settings.log_level,
        log_file_path=settings.log_file_path,
    )
    logger = get_logger("wanderlust.api")

    application = FastAPI(
        title=settings.api_title,
        version=settings.api_version,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(trips_router)
    application.include_router(itineraries_router)

    @application.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request,
        error: HTTPException,
    ) -> JSONResponse:
        if request.url.path.startswith("/api/"):
            log_event(
                logger,
                "warning",
                "http_exception",
                path=request.url.path,
                method=request.method,
                status_code=error.status_code,
                detail=error.detail,
            )
            return JSONResponse(
                status_code=error.status_code,
                content={
                    "success": False,
                    "data": None,
                    "error": error.detail,
                    "meta": None,
                },
            )
        raise error

    @application.get("/health", tags=["health"])
    async def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    return application


app = create_app()
