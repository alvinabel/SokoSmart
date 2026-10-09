"""FastAPI application factory for the AgroBasket marketplace service."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from shared import ApiError, get_config
from shared.categories import CATEGORIES
from shared.mongo import COLLECTIONS, ensure_indexes

from .core.mongo import get_db
from .routers import (
    bids,
    categories,
    favorites,
    listings,
    messages,
    notifications,
    orders,
    profile,
    reviews,
)

logger = logging.getLogger("agrobasket.api")

ROUTERS = (listings, categories, favorites, bids, orders, reviews, notifications, messages, profile)


def _seed_categories(db) -> None:
    """Ensure the storefront always has categories, even before seeders run."""
    coll = db[COLLECTIONS["categories"]]
    for cat in CATEGORIES:
        coll.update_one({"slug": cat["slug"]}, {"$setOnInsert": cat}, upsert=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = get_db()
    try:
        ensure_indexes(db)
    except Exception:  # pragma: no cover - best effort; mongomock/atlas quirk tolerance
        logger.warning("could not ensure Mongo indexes on boot")
    _seed_categories(db)
    yield


def create_app() -> FastAPI:
    cfg = get_config()

    app = FastAPI(
        title="AgroBasket Marketplace API",
        version="1.0.0",
        description=(
            "REST API for the AgroBasket agricultural produce marketplace. "
            "Authenticate with a Bearer access token issued by the identity service "
            "(`POST /api/auth/login`)."
        ),
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cfg.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    for module in ROUTERS:
        app.include_router(module.router, prefix="/api/v1")

    @app.get("/", tags=["meta"])
    def root():
        return {
            "service": "agrobasket-api",
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/api/health",
        }

    @app.get("/api/health", tags=["meta"])
    def health():
        get_db().command("ping")
        return {"status": "ok", "service": "agrobasket-api", "env": cfg.app_env}

    @app.exception_handler(ApiError)
    async def api_error_handler(_request: Request, exc: ApiError):
        return JSONResponse(status_code=exc.status_code, content=exc.to_dict())

    return app