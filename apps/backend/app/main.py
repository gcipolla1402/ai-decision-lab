from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.core.config import settings
from app.core.errors import AppError

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
logger = logging.getLogger("ai_decision_lab")

app = FastAPI(
    title="AI Decision Lab API",
    version="0.1.0",
    description="Personal demonstration API for synthetic document analysis and routing.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.allowed_origins),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
app.include_router(router)


@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    logger.warning(
        "request_failed error_code=%s provider=%s stage=%s status_code=%s",
        exc.error_code,
        exc.provider or "application",
        exc.stage or "request",
        exc.status_code,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.public_message, "error_code": exc.error_code},
    )


@app.exception_handler(Exception)
async def unexpected_error_handler(_: Request, __: Exception) -> JSONResponse:
    # Deliberately omit exception details: provider errors can contain sensitive metadata.
    logger.error("Unexpected request failure")
    return JSONResponse(status_code=500, content={"detail": "Unexpected server error."})

