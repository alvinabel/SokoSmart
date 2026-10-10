"""FastAPI application factory for the AgroBasket marketplace service."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from shared import ApiError, get_config
from shared.categories import CATEGORIES
from shared.db import get_conn
from shared.schema import ensure_schema

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
    for cat in CATEGORIES:
        db.execute(
            "INSERT INTO categories (slug, name, emoji, color) VALUES (%s, %s, %s, %s) "
            "ON CONFLICT (slug) DO NOTHING",
            (cat["slug"], cat.get("name", cat["slug"]), cat.get("emoji", "🥬"), cat.get("color", "#4CAF50")),
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    with get_conn() as db:
        ensure_schema(db)
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
        with get_conn() as db:
            db.execute("SELECT 1")
        return {"status": "ok", "service": "agrobasket-api", "env": cfg.app_env}

    @app.exception_handler(ApiError)
    async def api_error_handler(_request: Request, exc: ApiError):
        return JSONResponse(status_code=exc.status_code, content=exc.to_dict())

    return app
